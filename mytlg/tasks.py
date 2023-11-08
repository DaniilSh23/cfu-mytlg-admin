import datetime
import hashlib
import json
import time

import pytz
from celery import shared_task
from langchain.embeddings import OpenAIEmbeddings

from cfu_mytlg_admin.settings import MY_LOGGER, TIME_ZONE, BOT_TOKEN
from mytlg.api_requests import AccountsServiceRequests
from posts.services.text_process_service import TextProcessService
from mytlg.servises.categories_service import CategoriesService
from mytlg.servises.bot_users_service import BotUsersService
from mytlg.servises.news_posts_service import NewsPostsService
from mytlg.servises.tlg_accounts_service import TlgAccountsService
from mytlg.servises.account_subscription_tasks_service import AccountsSubscriptionTasksService
from mytlg.servises.bot_settings_service import BotSettingsService
from mytlg.servises.interests_service import InterestsService
from mytlg.servises.scheduled_post_service import ScheduledPostsService
from mytlg.models import Channels, AccountsSubscriptionTasks, BotSettings
from mytlg.utils import send_gpt_interests_proc_rslt_to_tlg, send_err_msg_for_user_to_telegram, send_message_by_bot, \
    bot_command_for_start_or_stop_account

text_processor = TextProcessService()


@shared_task
def scheduled_task_example():
    """
    Пример отложенной задачи, которая печатает в консоль.
    """
    time.sleep(5)
    print(f'Привет мир, я отложенная задача. Сейчас: {datetime.datetime.utcnow()}')


@shared_task
def gpt_interests_processing(interests, tlg_id):
    # TODO: требует рефакторинга. Нужно разделить подбор категорий для интересов и формирование эмбеддингов для них
    """
    Обработка интересов пользователя, через GPT модели.
    interests - список со словарями, где лежат данные об интересах
    tlg_id - Telegram ID пользователя
    """
    MY_LOGGER.info('Запускаем задачу celery по обработке интересов пользователя')
    MY_LOGGER.debug('Складываем общий список из категорий в строку')
    categories_str = CategoriesService.convert_category_list_to_string()

    MY_LOGGER.debug('Получаем объект BotUser и очищаем связи Many2Many для каналов и тем')
    bot_usr = BotUsersService.clear_bot_users_category_and_channels(tlg_id)

    themes_rslt = list()
    prompt = BotSettingsService.get_bot_settings_by_key(key='prompt_for_interests_category')
    for i_interest in interests:
        # Пилим эмбеддинги для интереса
        MY_LOGGER.debug(f'Пилим эмбеддинги для интереса: {i_interest.get("interest")}')
        # TODO: эту хуйню надо в try-except, но я не вьехал че там экзептиться может, потому что я уже заебался и выпил
        embeddings = OpenAIEmbeddings(max_retries=2)

        # Cклеиваем эмбеддинги через пробел (методу join нужна str, а не float, поэтому тут map)
        i_interest["embedding"] = ' '.join(
            map(lambda elem: str(elem), embeddings.embed_query(text=i_interest.get("interest")))
        )

        MY_LOGGER.debug(f'Шлём запрос к gpt для определения категории интереса: {i_interest.get("interest")!r}')
        gpt_rslt = text_processor.ask_the_gpt(
            base_text=categories_str,
            query=f'Подбери подходящую тематику для следующего интереса пользователя: {i_interest.get("interest")}',
            system=prompt,
            temp=0.3,
        )
        if not gpt_rslt:
            MY_LOGGER.error('Неудачный запрос к API OpenAI')
            send_err_msg_for_user_to_telegram(err_msg='😔 Серверы ИИ перегружены, не удалось подобрать подходящие для '
                                                      'Вас темы. Пожалуйста, попробуйте позже 🔄', tlg_id=tlg_id)
            return

        MY_LOGGER.debug(f'Получили ответ от GPT {gpt_rslt!r} по интересу пользователя {i_interest.get("interest")!r}')
        category, gpt_rslt = CategoriesService.create_category_from_gpt_result(gpt_rslt, i_interest)
        bot_usr.category.add(category)
        i_interest["category"] = category
        themes_rslt.append(gpt_rslt.lower())
        time.sleep(1)  # Задержечка, чтобы модель OpenAI не охуела от частоты запросов
        # TODO: надо дописать использование другой модели и чередование их между интересами

    MY_LOGGER.debug('Создаём за раз несколько записей в БД для модели Interests')
    InterestsService.bulk_create_interests(bot_usr, interests)

    MY_LOGGER.debug('Отправка в телеграм подобранных тем.')
    send_gpt_interests_proc_rslt_to_tlg(gpt_rslts=themes_rslt, tlg_id=tlg_id)

    MY_LOGGER.info('Окончание работы задачи celery по обработке интересов пользователя.')


@shared_task
def scheduled_task_for_send_post_to_users():
    """
    Задача по расписанию для отправки новостных постов пользователям.
    """
    MY_LOGGER.info('Вызвана задача по отправке новостных постов пользователям')

    # Достаём посты, которые должны быть отправлены
    posts = ScheduledPostsService.get_posts_that_need_to_send()
    # Получаем промт для перевода и температуру
    prompt = BotSettingsService.get_bot_settings_by_key(key='promt_for_detect_and_translate_posts_language')
    temp = float(BotSettingsService.get_bot_settings_by_key(key='temp_for_ai_language_detect_and_translate'))
    # Получаем пользователей
    bot_user_ids = set(posts.values_list('bot_user', flat=True))
    bot_users = BotUsersService.filter_bot_users_by_ids(bot_user_ids)
    interests_ids = list()  # Список для хранения айди интересов

    # Поочереди достаём посты для конкретного юзера и отправляем их сокращенный вариант
    for i_usr in bot_users:
        i_usr_posts = posts.filter(bot_user=i_usr)
        posts_str = '🗞 Есть новости для Вас:'
        for i_post in i_usr_posts:
            # Если длина сообщения с кратким содержанием постов превышает лимит телеграмм
            if len(i_post.news_post.short_text) + len(posts_str) >= 2000:
                send_result = send_message_by_bot(chat_id=i_usr.tlg_id, text=f"{posts_str}\n{'➖' * 10}",
                                                  disable_notification=True)
                if not send_result:
                    MY_LOGGER.warning(f'Не удалось отправить часть сокращённых вариантов постов юзеру {i_usr!r}')
                    break
                posts_str = '🗞 продолжение...'

            original_short_text = i_post.news_post.short_text
            short_text = text_processor.gpt_text_language_detection_and_translate(prompt=prompt,
                                                                                  text=original_short_text,
                                                                                  user_language_code=i_usr.language_code,
                                                                                  temp=temp)
            posts_str = (f"{posts_str}\n\n⭐️ {i_post.interest.short_interest()}\n📰 {short_text}\n🔗 "
                         f"Оригинал: {i_post.news_post.post_link}\n{'➖' * 10}")

            # Добавляем id интереса в общий список
            interests_ids.append(i_post.interest.id)

        MY_LOGGER.debug(f'Отправляем сокращенный вариант постов юзеру {i_usr!r}')
        send_result = send_message_by_bot(chat_id=i_usr.tlg_id, text=posts_str)
        if not send_result:
            MY_LOGGER.warning(f'Не удалось отправить сокращенный вариант постов юзеру {i_usr!r}')
            continue

        # Обновляем флаг is_sent у запланированных к отправке постов
        i_usr_posts.update(is_sent=True)

    # Обновляем дату и время крайней отправки у интересов
    InterestsService.update_date_and_time_interests_last_sending_time(interests_ids)
    MY_LOGGER.info('Окончание задачи по отправке новостных постов пользователям')


@shared_task
def subscription_to_new_channels():
    """
    Таск селери для подписки аккаунтов на новые каналы.
    """
    MY_LOGGER.info('Запущен таск селери по подписке аккаунтов на новые каналы.')

    max_ch_per_acc = int(BotSettings.objects.get(key='max_channels_per_acc').value)

    # Берём аккаунты, у которых число каналов < чем переменная max_ch_per_acc
    acc_qset = TlgAccountsService.get_tlgaccounts_that_dont_have_max_channels(max_ch_per_acc)

    # Достаём таски на подписку, которые в работе и имеют связанные каналы
    subs_tasks_qset = AccountsSubscriptionTasksService.get_subscription_tasks_in_works()

    # # Формируем список с ID каналов, на которые подписываться не надо.
    # Тут исключаем каналы, на которые сейчас подписываются аккаунты.
    excluded_ids = [channel.id for task in subs_tasks_qset
                    for channel in task.channels.all()]
    # Тут исключаем каналы по аккаунтам, которые уже на них подписаны.
    excluded_ids = TlgAccountsService.exclude_allready_subscripted_channels(excluded_ids)
    # Достаём каналы и распределяем их по аккаунтам
    ch_lst = Channels.objects.filter(is_ready=False).exclude(id__in=excluded_ids).only("id", "channel_link")

    ##########
    # INFO: Ниже изменения:
    #
    # старый код отправляет от лица бота сообщение аккаунту с json файлом, в котором лежит
    # информация на какие каналы должен подписаться аккаунт.
    #
    # Новый код отправляет немного другой json одним http
    # запросом на адрес API веб-приложения, которое управляет аккаунтами.
    #
    # Для всего этого я просто закомментирую сам запрос к API Telegram для отправки сообщения аккаунту от лица бота и
    # в цикле соберу данные для подписок всех аккаунтов в один словарь и затем кину одним запросом к веб-приложухе,
    # которая управляет аккаунтами. Ранее же, через бота, каждому аккаунту данные отправлялись разными запросами к
    # API Telegram (на каждой итерации цикла, теперь же после всех итераций будет лететь запрос к API веб-приложухи).
    #
    # Вроде как понятно расписал, но хз я чутка заебался уже.
    ##########

    # Это новый словарик, в который мы соберем данные для веб-приложения
    start_subscription_general_data = dict(
        token=BOT_TOKEN,
        subs_data=[],
    )

    MY_LOGGER.debug(f'Итерируемся по {len(acc_qset)} для создания задач на подписку.')
    for i_indx, i_acc in enumerate(acc_qset):
        MY_LOGGER.debug(f'Итерируемся по {i_indx+1} аккаунту из {len(acc_qset)}')
        ch_available_numb = max_ch_per_acc - i_acc.channels.count()  # На сколько каналов может подписаться акк
        i_acc_channels_lst = ch_lst[:ch_available_numb]  # Срезаем нужные каналы для аккаунта в отдельный список

        # Данные для подписки итерируемому аккаунту
        acc_task_data = {
            'acc_pk': i_acc.pk,
            'channels': [
                {"channel_pk": i_ch.pk, "channel_link": i_ch.channel_link}
                for i_ch in i_acc_channels_lst
            ]
        }

        # Создаём таск на подписку
        MY_LOGGER.debug(f'Создаём в БД запись о задаче аккаунту PK = {i_acc.pk}')
        acc_task = AccountsSubscriptionTasks.objects.create(
            total_channels=len(i_acc_channels_lst),
            tlg_acc=i_acc,
            initial_data=json.dumps(acc_task_data),
        )
        acc_task.channels.add(*i_acc_channels_lst)

        # Устанавливаем PK таска на подписку и пополняем общий словарь
        acc_task_data["subs_task_pk"] = acc_task.pk
        start_subscription_general_data['subs_data'].append(acc_task_data)

        # Отрезаем из общего списка каналы, которые забрал аккаунт и проверяем закончился ли список с каналами
        ch_lst = ch_lst[ch_available_numb:]
        MY_LOGGER.debug(f'Осталось {len(ch_lst)} каналов в общем списки для подписки на них.')
        if len(ch_lst) <= 0 or i_indx + 1 == len(acc_qset):
            MY_LOGGER.debug('Список каналов закончился или закончился список аккаунтов, которые могут подписываться,'
                            ' кидаем запрос в сервис аккаунтов для старта подписки и останавливаем цикл итерации по '
                            'аккаунтам')
            req_rslt, resp_info = AccountsServiceRequests.post_req_for_start_subscription(
                req_data=start_subscription_general_data
            )
            if not req_rslt:
                msg = f'Не удалось отправить запрос для старта подписки на каналы | RESPONSE: {resp_info}'
                MY_LOGGER.error(msg)
            else:
                msg = f'Таск по отправке аккаунтам задач подписаться на каналы завершен. | RESPONSE: {resp_info}'
                MY_LOGGER.success(msg)
            return msg


@shared_task
def start_or_stop_accounts(bot_command='start_acc'):
    """
    Отложенная задача celery для старта или остановки аккаунтов телеграмм.
    """
    MY_LOGGER.debug(f'Запущена задача по отправке боту команды для старта или стопа аккаунтов')
    tlg_accounts = TlgAccountsService.get_tlg_accounts_for_start_or_stop()
    bot_admin = BotSettingsService.get_bot_settings_by_key(key='bot_admins')
    for i_acc in tlg_accounts:
        bot_command_for_start_or_stop_account(instance=i_acc, bot_command=bot_command, bot_admin=bot_admin)
        time.sleep(0.5)  # Небольшая задержка, чтобы бот успел запустить асинк таски
    MY_LOGGER.debug('Задача завершена')


@shared_task
def what_was_interesting():
    """
    Таск, который раз в неделю спрашивает, что было нового и интересного.
    """
    MY_LOGGER.info('Запущен таск по опросу, что было интересного у пользователей')

    # Достаём юзеров из БД и отправляем им сообщение
    users = BotUsersService.get_bot_users_only_tlg_id()
    for i_usr in users:
        MY_LOGGER.debug(f'Спрашиваем юзера с tlg_id == {i_usr.tlg_id!r}')
        send_message_by_bot(
            chat_id=int(i_usr.tlg_id),
            text='👋 Привет!\nКак прошли Ваши выходные?\n\n⭐️ Возможно встретилось что-то новое и интересное?'
                 '\n💡 Можете рассказать об этом и я подберу для Вас подходящий контент'
                 '\n<tg-spoiler>$$$what_was_interesting</tg-spoiler>'
        )

    MY_LOGGER.info('Закончен таск по опросу, что было интересного у пользователей')


@shared_task
def search_content_by_new_interest(interest, usr_tlg_id):
    """
    Задачка селери по поиску контента для функции опроса, что встретилось нового и интересного.
    """
    MY_LOGGER.info(f'Запущена задача селери по поиску контента для юзера с tlg_id=={usr_tlg_id!r} '
                   f'(функция "что встретилось нового и интересного").')

    # Достаём из БД объект юзера
    bot_user_obj = BotUsersService.get_bot_user_by_tg_id(tlg_id=usr_tlg_id)
    # Достаём или создаём в БД категорию "тест" (в нее сливаем все неотсортированные интересы)
    category, created = CategoriesService.get_or_create(
        category_name='тест',
        defaults={'category_name': 'тест'}
    )
    if created:
        MY_LOGGER.info('Создана категория "тест".')

    # Пилим эмбеддинги для интереса
    MY_LOGGER.debug(f'Пилим эмбеддинги для интереса: {interest}')
    # TODO: эту хуйню надо в try-except, но я не вьехал че там экзептиться может, потому что я уже заебался и выпил
    embeddings = OpenAIEmbeddings(max_retries=2)

    # Cклеиваем эмбеддинги через пробел (методу join нужна str, а не float, поэтому тут map)
    embedding_str = ' '.join(
        map(lambda elem: str(elem), embeddings.embed_query(text=interest))
    )
    # Записываем интерес в БД
    new_interest = InterestsService.create(bot_user_obj, category, embedding_str, interest)
    # Ищем релевантный контент для интереса пользователя
    posts = NewsPostsService.get_posts_by_sending_period()
    for i_post in posts:

        # TODO: забыл написать вычисление сходства поста и интереса по векторным расстояниям

        # Проверка, что пост ранее не отправлялся юзеру и не спланирован к отправке в будущем
        scheduled_posts_qset = ScheduledPostsService.get_scheduled_posts_by_bot_user_and_news_post_for_task(
            bot_user_obj, i_post)
        if len(scheduled_posts_qset) > 1:
            # Изменяем дату и время отправки для неотправленных постов на "сейчас"
            ScheduledPostsService.update_when_send_for_not_sended_posts(scheduled_posts_qset)
            continue

        # Планируем пост к отправке
        ScheduledPostsService.scheduling_post_for_sending(
            post=i_post,
            bot_usr=bot_user_obj,
            interest=new_interest,
        )

    MY_LOGGER.info(f'Конец задачи селери по поиску контента для юзера с tlg_id=={usr_tlg_id!r}')


@shared_task
def sending_post_selections():
    """
    Отправка пользователям уведомлений о том, что для них есть подборки постов.
    """
    MY_LOGGER.info('Старт задачи по формированию подборки постов для пользователей и отправки уведомления в ТГ')

    # Заготовки
    time_now = datetime.datetime.now(tz=pytz.timezone(TIME_ZONE)).strftime('%H:%M:%S')  # DT для создания хэша
    interests_ids = list()  # Список для хранения айди интересов

    # Достаём посты, которые должны быть отправлены
    posts = ScheduledPostsService.get_posts_that_need_to_send()

    # Получаем пользователей
    bot_user_ids = set(posts.values_list('bot_user', flat=True))
    bot_users = BotUsersService.get_bot_users_id_and_tlg_id_by_ids(bot_user_ids)

    # Поочереди достаём посты для конкретного юзера и отправляем их сокращенный вариант
    for i_usr in bot_users:
        if InterestsService.check_if_bot_user_have_interest(i_usr.id):
            selection_hash = hashlib.md5(f'{time_now}{i_usr.tlg_id}'.encode('utf-8')).hexdigest()
            i_usr_posts = posts.filter(bot_user=i_usr)
            i_usr_posts.update(selection_hash=selection_hash)
            posts_str = (f'🗞 <b>Есть новости для Вас</b>\n<i>(по состоянию на {time_now})</i>\n\n\n\n'
                         f'<tg-spoiler>$$$news_collection {selection_hash}</tg-spoiler>')

            # Добавляем id интереса в общий список
            interests_ids.extend(
                i_post.interest.id for i_post in i_usr_posts if i_post.interest
            )
            MY_LOGGER.debug(f'Отправляем уведомление о выходе подборки постов юзеру: {i_usr!r}')
            send_result = send_message_by_bot(chat_id=i_usr.tlg_id, text=posts_str)
            if not send_result:
                MY_LOGGER.warning(f'Не удалось уведомление о выходе подборки постов юзеру: {i_usr!r}')
                continue

            # Обновляем флаг is_sent у запланированных к отправке постов
            i_usr_posts.update(is_sent=True)

    # Обновляем дату и время крайней отправки у интересов
    InterestsService.update_date_and_time_interests_last_sending_time(interests_ids)
    MY_LOGGER.info('Конец задачи по формированию подборки постов для пользователей и отправки уведомления в ТГ')
