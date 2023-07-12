import datetime
from typing import List
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.gpt_processing import ask_the_gpt
from mytlg.models import Themes, Channels, BotUser, SubThemes
from mytlg.utils import send_gpt_interests_proc_rslt_to_tlg


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

    MY_LOGGER.debug(f'Складываем общий список из тем и подтем в строку')
    themes_qset = Themes.objects.all()
    sub_themes_qset = SubThemes.objects.all()
    all_themes_lst = [i_theme.theme_name for i_theme in themes_qset]
    all_themes_lst.extend([i_sub_th.sub_theme_name for i_sub_th in sub_themes_qset])
    themes_str = '\n'.join([i_theme for i_theme in all_themes_lst])

    MY_LOGGER.debug(f'Получаем объект BotUser и очищаем связи Many2Many для каналов и тем')
    bot_usr = BotUser.objects.get(tlg_id=tlg_id)
    bot_usr.themes.clear()
    bot_usr.channels.clear()

    themes_rslt = list()
    for i_interest in interests:
        MY_LOGGER.debug(f'Шлём запрос к gpt по интересу: {i_interest!r}')
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
        MY_LOGGER.debug(f'Получили ответ от GPT {gpt_rslt!r} по интересу пользователя {i_interest!r}')
        MY_LOGGER.debug(f'Привязываем пользователя к подтеме и каналам')
        try:
            rel_theme = Themes.objects.get(theme_name=gpt_rslt.lower())
            bot_usr.themes.add(rel_theme)
            rel_channels = Channels.objects.filter(theme=rel_theme)[:5]
        except ObjectDoesNotExist:
            try:
                rel_theme = SubThemes.objects.get(sub_theme_name=gpt_rslt.lower())
                bot_usr.sub_themes.add(rel_theme)
                rel_channels = Channels.objects.filter(sub_theme=rel_theme)[:5]
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'В БД не найдена тема или подтема: {gpt_rslt!r}. Пользователь не привязан.')
                continue
        themes_rslt.append(gpt_rslt.lower())
        [bot_usr.channels.add(i_ch) for i_ch in rel_channels]

    MY_LOGGER.debug(f'Отправка в телеграм подобранных тем и каналов')
    send_gpt_interests_proc_rslt_to_tlg(gpt_rslts=themes_rslt, tlg_id=tlg_id)

    MY_LOGGER.info(f'Окончание работы задачи celery по обработке интересов пользователя, через GPT модель.')
