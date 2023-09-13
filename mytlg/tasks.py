import datetime
import json
import time
from io import BytesIO
from typing import List
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.gpt_processing import ask_the_gpt
from mytlg.models import Categories, Channels, BotUser, NewsPosts, TlgAccounts, AccountsSubscriptionTasks, BotSettings
from mytlg.utils import send_gpt_interests_proc_rslt_to_tlg, send_err_msg_for_user_to_telegram, send_message_by_bot, \
    send_file_by_bot, bot_command_for_start_or_stop_account


@shared_task
def scheduled_task_example():
    """
    Пример отложенной задачи, которая печатает в консоль.
    """
    time.sleep(5)
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
    themes_qset = Categories.objects.all()
    all_themes_lst = [i_theme.category_name for i_theme in themes_qset]
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
                   'выбирай тематику строго из того списка, который получил. Если интерес пользователя не подходит '
                   'ни под одну из предоставленных тебе тематик, то пришли в ответ только фразу no themes и никакого '
                   'больше текста.',
            temp=0.3,
        )
        if not gpt_rslt:
            MY_LOGGER.error(f'Неудачный запрос к API OpenAI')
            send_err_msg_for_user_to_telegram(err_msg='😔 Серверы ИИ перегружены, не удалось подобрать подходящие для '
                                                      'Вас темы. Пожалуйста, попробуйте позже 🔄', tlg_id=tlg_id)
            return

        MY_LOGGER.debug(f'Получили ответ от GPT {gpt_rslt!r} по интересу пользователя {i_interest!r}')
        if gpt_rslt == 'no themes':
            MY_LOGGER.info(f'GPT не определил тем для интереса пользователя: {i_interest!r} и прислал {gpt_rslt!r}')
            gpt_rslt = 'gpt не определил тему'
        else:
            MY_LOGGER.debug(f'Привязываем пользователя к подтеме и каналам')
            try:
                rel_theme = Categories.objects.get(category_name=gpt_rslt.lower())
                bot_usr.themes.add(rel_theme)
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'В БД не найдена категория: {gpt_rslt!r}. Пользователь не привязан.')
                continue
        themes_rslt.append(gpt_rslt.lower())

    MY_LOGGER.debug(f'Отправка в телеграм подобранных тем.')
    send_gpt_interests_proc_rslt_to_tlg(gpt_rslts=themes_rslt, tlg_id=tlg_id)

    MY_LOGGER.info(f'Окончание работы задачи celery по обработке интересов пользователя, через GPT модель.')


@shared_task
def scheduled_task_for_send_post_to_users():
    """
    Задача по расписанию для отправки новостных постов пользователям.
    """
    MY_LOGGER.info(f'Вызвана задача по отправке новостных постов пользователям')

    news_posts_qset = NewsPosts.objects.filter(is_sent=False).only('text', 'channel').prefetch_related('channel')
    mailing_users_set = set()

    MY_LOGGER.debug(f'Отправляем посты')
    for i_post in news_posts_qset:
        # Достаём юзеров, связанных с этим каналов
        bot_users_qset = BotUser.objects.filter(themes=i_post.channel.theme).only('tlg_id')
        # Отправляем по очереди всем этим юзерам новостной пост
        for i_bot_user in bot_users_qset:
            send_message_by_bot(chat_id=i_bot_user.tlg_id, text=i_post.text, disable_notification=True)
            mailing_users_set.add(i_bot_user.tlg_id)
        # Когда итерация по новостному посту закончена, ставим в БД посту флаг is_sent=True
        i_post.is_sent = True
        i_post.save()

    # Отправляем пользователям уведомление, что для них есть новый контент
    MY_LOGGER.debug(f'Отправляем уведомления пользователям')
    for _ in range(len(mailing_users_set)):
        send_message_by_bot(chat_id=mailing_users_set.pop(),
                            text='🗞 Для Вас есть свежие новости.', disable_notification=False)

    MY_LOGGER.info(f'Окончание задачи по отправке новостных постов пользователям')


@shared_task
def subscription_to_new_channels():
    """
    Таск селери для подписки аккаунтов на новые каналы.
    """
    MY_LOGGER.info(f'Запущен таск селери по подписке аккаунтов на новые каналы.')

    max_ch_per_acc = int(BotSettings.objects.get(key='max_channels_per_acc').value)

    # Берём аккаунты, у которых число каналов < чем переменная max_ch_per_acc
    # TODO: тут додумать only()
    acc_qset = (TlgAccounts.objects.annotate(num_ch=Count('channels')).filter(num_ch__lt=max_ch_per_acc, is_run=True)
                .only("channels", "acc_tlg_id").prefetch_related("channels"))

    # Достаём таски на подписку, которые в работе и имеют связанные каналы
    subs_tasks_qset = (AccountsSubscriptionTasks.objects.exclude(channels=None).filters(status='at_work')
                       .only('channels', 'tlg_acc'))

    # # Формируем список с ID каналов, на которые подписываться не надо.
    # Тут исключаем каналы, на которые сейчас подписываются аккаунты.
    excluded_ids = [channel.id for task in subs_tasks_qset
                    for channel in task.channels.all()]
    # Тут исключаем каналы по аккаунтам, которые уже на них подписаны.
    accs = TlgAccounts.objects.filter(is_run=True).only('channels').prefetch_related('channels')
    for i_acc in accs:
        excluded_ids.extend([i_ch.id for i_ch in i_acc.channels])
    excluded_ids = list(set(excluded_ids))  # Избавляемся от дублей

    # Достаём каналы и распределяем их по аккаунтам
    ch_lst = Channels.objects.filter(is_ready=False).exclude(id__in=excluded_ids).only("id", "channel_link")
    for i_acc in acc_qset:
        ch_available_numb = max_ch_per_acc - i_acc.channels.count()  # На сколько каналов может подписаться акк
        i_acc_channels_lst = ch_lst[:ch_available_numb]  # Срезаем нужные каналы для аккаунта в отдельный список

        MY_LOGGER.debug(f'Создаём в БД запись о задаче аккаунту')
        # Команда для бота (её данные)
        command_data = {
            "cmd": "subscribe_to_channels",
            "data": [(i_ch.pk, i_ch.channel_link) for i_ch in i_acc_channels_lst],
        }
        acc_task = AccountsSubscriptionTasks.objects.create(
            total_channels=len(i_acc_channels_lst),
            tlg_acc=i_acc,
            initial_data=json.dumps(command_data),
        )
        acc_task.channels.add(*i_acc_channels_lst)

        MY_LOGGER.debug(f'Отправляем через бота задачу аккаунту')
        command_data['task_pk'] = acc_task.pk
        task_is_set = send_file_by_bot(
            chat_id=i_acc.acc_tlg_id,
            caption=f"/subscribe_to_channels",
            file=BytesIO(json.dumps(command_data).encode(encoding='utf-8')),
            file_name='command_data.txt',
        )
        if not task_is_set:
            MY_LOGGER.warning(f'Не удалось поставить аккаунту задачу! {i_acc!r}')
            acc_task.delete()  # Удаляем из БД задачу аккаунта
            continue

        ch_lst = ch_lst[ch_available_numb:]  # Отрезаем из общего списка каналы, которые забрал аккаунт
        if len(ch_lst) < 0:
            MY_LOGGER.debug('Список каталов закончился, останавливаем цикл итерации по аккаунтам')
            break

    MY_LOGGER.info(f'Таск по отправке аккаунтам задач подписаться на каналы завершена.')


@shared_task
def start_or_stop_accounts(bot_command='start_acc'):
    """
    Отложенная задача celery для старта или остановки аккаунтов телеграмм.
    """
    MY_LOGGER.debug(f'Запущена задача по отправке боту команды для старта или стопа аккаунтов')
    tlg_accounts = TlgAccounts.objects.filter(is_run=True).only("id", "session_file", "proxy").prefetch_related("proxy")
    bot_admin = BotSettings.objects.get(key='bot_admins').value.split()[0]
    for i_acc in tlg_accounts:
        bot_command_for_start_or_stop_account(instance=i_acc, bot_command=bot_command, bot_admin=bot_admin)
        time.sleep(0.5)  # Небольшая задержка, чтобы бот успел запустить асинк таски
    MY_LOGGER.debug(f'Задача завершена')
