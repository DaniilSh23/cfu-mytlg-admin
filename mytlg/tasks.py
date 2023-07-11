import datetime
from typing import List
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.gpt_processing import ask_the_gpt
from mytlg.models import Themes, Channels, BotUser


@shared_task
def scheduled_task_example():
    """
    Пример отложенной задачи, которая печатает в консоль.
    """
    print(f'Привет мир, я отложенная задача. Сейчас: {datetime.datetime.utcnow()}')


@shared_task
def gpt_interests_processing(interests: List, tlg_id: str):
    """
    Обработка интересов пользователя, через GPT модель.
    interests - список с формулировками интересов пользователя
    tlg_id - Telegram ID пользователя
    """
    MY_LOGGER.info('Запускаем задачу celery по отбору тематик по формулировкам пользователя')
    themes = Themes.objects.all()
    themes_str = '\n'.join([i_theme.theme_name for i_theme in themes])

    MY_LOGGER.debug(f'Получаем объект BotUser и очищаем связи Many2Many для каналов и тем')
    bot_usr = BotUser.objects.get(tlg_id=tlg_id)
    bot_usr.themes.clear()
    bot_usr.channels.clear()

    for i_interest in interests:
        gpt_rslt = ask_the_gpt(
            base_text=themes_str,
            query=f'Подбери подходящую тематику для следующего интереса пользователя: {i_interest}',
            system='Ты ответственный помощник и твоя задача - это классификация интересов пользователей по '
                   'определённым тематикам. На вход ты будешь получать данные с информацией для ответа пользователю - '
                   'это список тематик (каждая тематика с новой строки) и запрос пользователя, который будет содержать '
                   'формулировку его интереса. Твоя задача определить только одну тематику из переданного списка, '
                   'которая с большей вероятностью подходит под интерес пользователя и написать в ответ только эту '
                   'тематику и никакого больше текста в твоём ответе не должно быть. Не придумывай ничего от себя, '
                   'выбирай тематику строго из того списка, который получил.'
        )
        MY_LOGGER.debug(f'Получили ответ от GPT {gpt_rslt!r} по такому интересу пользователя {i_interest!r}')

        try:
            rel_theme = Themes.objects.get(theme_name=gpt_rslt.lower())
            bot_usr.themes.add(rel_theme)
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не найдена в БД тематика: {gpt_rslt!r}')
            continue

        MY_LOGGER.debug(f'Привязываем пользователя к тематике и каналам')
        rel_channels = Channels.objects.filter(theme=rel_theme)[:5]
        [bot_usr.channels.add(i_ch) for i_ch in rel_channels]

    MY_LOGGER.info(f'Окончание работы задачи celery по обработке интересов пользователя, через GPT модель.')
