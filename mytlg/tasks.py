import datetime
import hashlib
import json
import time
from io import BytesIO
from typing import List, Dict

import pytz
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from langchain.embeddings import OpenAIEmbeddings

from cfu_mytlg_admin.settings import MY_LOGGER, TIME_ZONE
from mytlg.common import scheduling_post_for_sending
from mytlg.gpt_processing import ask_the_gpt, gpt_text_language_detection_and_translate
from mytlg.models import Categories, Channels, BotUser, NewsPosts, TlgAccounts, AccountsSubscriptionTasks, BotSettings, \
    Interests, ScheduledPosts
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
def gpt_interests_processing(interests, tlg_id):
    # TODO: требует рефакторинга. Нужно разделить подбор категорий для интересов и формирование эмбеддингов для них
    """
    Обработка интересов пользователя, через GPT модели.
    interests - список со словарями, где лежат данные об интересах
    tlg_id - Telegram ID пользователя
    """
    MY_LOGGER.info('Запускаем задачу celery по обработке интересов пользователя')

    MY_LOGGER.debug(f'Складываем общий список из категорий в строку')
    categories_qset = Categories.objects.all()
    all_categories_lst = [category.category_name for category in categories_qset]
    categories_str = '\n'.join([category for category in all_categories_lst])

    MY_LOGGER.debug(f'Получаем объект BotUser и очищаем связи Many2Many для каналов и тем')
    bot_usr = BotUser.objects.get(tlg_id=tlg_id)
    bot_usr.category.clear()
    bot_usr.channels.clear()

    themes_rslt = list()
    prompt = BotSettings.objects.get(key='prompt_for_interests_category').value
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
        gpt_rslt = ask_the_gpt(
            base_text=categories_str,
            query=f'Подбери подходящую тематику для следующего интереса пользователя: {i_interest.get("interest")}',
            system=prompt,
            temp=0.3,
        )
        if not gpt_rslt:
            MY_LOGGER.error(f'Неудачный запрос к API OpenAI')
            send_err_msg_for_user_to_telegram(err_msg='😔 Серверы ИИ перегружены, не удалось подобрать подходящие для '
                                                      'Вас темы. Пожалуйста, попробуйте позже 🔄', tlg_id=tlg_id)
            return

        MY_LOGGER.debug(f'Получили ответ от GPT {gpt_rslt!r} по интересу пользователя {i_interest.get("interest")!r}')
        if gpt_rslt == 'no_themes':
            MY_LOGGER.info(f'GPT не определил тем для интереса пользователя: {i_interest.get("interest")!r} '
                           f'и прислал {gpt_rslt!r}. Привязываем юзера к категории тест')
            gpt_rslt = 'общее 🆕'
            category, created = Categories.objects.get_or_create(
                category_name='тест',
                defaults={"category_name": "тест"}
            )
        else:
            MY_LOGGER.debug(f'Привязываем пользователя к категории и каналам')
            try:
                category = Categories.objects.get(category_name=gpt_rslt.lower())
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'В БД не найдена категория: {gpt_rslt!r}. '
                                  f'Привязывем по стандарту к категории "тест".')
                category, created = Categories.objects.get_or_create(
                    category_name='тест',
                    defaults={"category_name": "тест"}
                )

        bot_usr.category.add(category)
        i_interest["category"] = category
        themes_rslt.append(gpt_rslt.lower())
        time.sleep(1)  # Задержечка, чтобы модель OpenAI не охуела от частоты запросов
        # TODO: надо дописать использование другой модели и чередование их между интересами

    MY_LOGGER.debug(f'Создаём за раз несколько записей в БД для модели Interests')
    interests_objs = []
    for interest in interests:
        interest['bot_user'] = bot_usr
        interests_objs.append(Interests(**interest))
    Interests.objects.bulk_create(interests_objs)

    MY_LOGGER.debug(f'Отправка в телеграм подобранных тем.')
    send_gpt_interests_proc_rslt_to_tlg(gpt_rslts=themes_rslt, tlg_id=tlg_id)

    MY_LOGGER.info(f'Окончание работы задачи celery по обработке интересов пользователя.')


@shared_task
def scheduled_task_for_send_post_to_users():
    """
    Задача по расписанию для отправки новостных постов пользователям.
    """
    MY_LOGGER.info(f'Вызвана задача по отправке новостных постов пользователям')

    # Достаём посты, которые должны быть отправлены
    posts = ScheduledPosts.objects.filter(
        is_sent=False,
        when_send__lte=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
    ).prefetch_related("bot_user").prefetch_related("news_post")

    # Получаем промт для перевода
    prompt = BotSettings.objects.get(key='promt_for_detect_and_translate_posts_language').value
    # Получаем пользователей
    bot_user_ids = set(posts.values_list('bot_user', flat=True))
    bot_users = BotUser.objects.filter(id__in=bot_user_ids)

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
                posts_str = f'🗞 продолжение...'

            original_short_text = i_post.news_post.short_text
            short_text = gpt_text_language_detection_and_translate(prompt=prompt,
                                                                   text=original_short_text,
                                                                   user_language_code=i_usr.language_code,
                                                                   temp=float(BotSettings.objects.get(
                                                                       key='temp_for_ai_language_detect_and_translate').value))
            posts_str = f"{posts_str}\n\n⭐️ {i_post.interest.short_interest()}\n📰 {short_text}\n🔗 Оригинал: {i_post.news_post.post_link}\n{'➖' * 10}"

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
    Interests.objects.filter(id__in=set(interests_ids)).update(
        last_send=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
    )

    MY_LOGGER.info(f'Окончание задачи по отправке новостных постов пользователям')


@shared_task
def subscription_to_new_channels():
    """
    Таск селери для подписки аккаунтов на новые каналы.
    """
    MY_LOGGER.info(f'Запущен таск селери по подписке аккаунтов на новые каналы.')

    max_ch_per_acc = int(BotSettings.objects.get(key='max_channels_per_acc').value)

    # Берём аккаунты, у которых число каналов < чем переменная max_ch_per_acc
    acc_qset = (TlgAccounts.objects.annotate(num_ch=Count('channels')).filter(num_ch__lt=max_ch_per_acc, is_run=True)
                .only("channels", "acc_tlg_id").prefetch_related("channels"))

    # Достаём таски на подписку, которые в работе и имеют связанные каналы
    subs_tasks_qset = (AccountsSubscriptionTasks.objects.filter(status='at_work', channels__isnull=False)
                       .only('channels', 'tlg_acc'))

    # # Формируем список с ID каналов, на которые подписываться не надо.
    # Тут исключаем каналы, на которые сейчас подписываются аккаунты.
    excluded_ids = [channel.id for task in subs_tasks_qset
                    for channel in task.channels.all()]
    # Тут исключаем каналы по аккаунтам, которые уже на них подписаны.
    accs = TlgAccounts.objects.filter(is_run=True).only('channels').prefetch_related('channels')
    for i_acc in accs:
        excluded_ids.extend([i_ch.id for i_ch in i_acc.channels.all()])
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
        if len(ch_lst) <= 0:
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


@shared_task
def what_was_interesting():
    """
    Таск, который раз в неделю спрашивает, что было нового и интересного.
    """
    MY_LOGGER.info(f'Запущен таск по опросу, что было интересного у пользователей')

    # Достаём юзеров из БД и отправляем им сообщение
    users = BotUser.objects.all().only('tlg_id')
    for i_usr in users:
        MY_LOGGER.debug(f'Спрашиваем юзера с tlg_id == {i_usr.tlg_id!r}')
        send_message_by_bot(
            chat_id=int(i_usr.tlg_id),
            text='👋 Привет!\nКак прошли Ваши выходные?\n\n⭐️ Возможно встретилось что-то новое и интересное?'
                 '\n💡 Можете рассказать об этом и я подберу для Вас подходящий контент'
                 '\n<tg-spoiler>$$$what_was_interesting</tg-spoiler>'
        )

    MY_LOGGER.info(f'Закончен таск по опросу, что было интересного у пользователей')


@shared_task
def search_content_by_new_interest(interest, usr_tlg_id):
    """
    Задачка селери по поиску контента для функции опроса, что встретилось нового и интересного.
    """
    MY_LOGGER.info(f'Запущена задача селери по поиску контента для юзера с tlg_id=={usr_tlg_id!r} '
                   f'(функция "что встретилось нового и интересного").')

    # Достаём из БД объект юзера
    bot_user_obj = BotUser.objects.get(tlg_id=usr_tlg_id)

    # Достаём или создаём в БД категорию "тест" (в нее сливаем все неотсортированные интересы)
    category, created = Categories.objects.get_or_create(
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
    new_interest = Interests.objects.create(
        interest=interest,
        embedding=embedding_str,
        bot_user=bot_user_obj,
        category=category,
        is_active=False,
        send_period='now',
        interest_type='whats_new',
    )
    MY_LOGGER.success(f'В БД создан новый интерес юзера {bot_user_obj!r} | PK интереса == {new_interest.pk!r}')

    # Ищем релевантный контент для интереса пользователя
    period = int(BotSettings.objects.get(key='period_for_what_was_interest_sec').value)
    period = datetime.datetime.fromtimestamp(float(period))
    posts = NewsPosts.objects.filter(created_at__gt=period).only('embedding', 'post_link', 'short_text')
    for i_post in posts:

        # TODO: забыл написать вычисление сходства поста и интереса по векторным расстояниям

        # Проверка, что пост ранее не отправлялся юзеру и не спланирован к отправке в будущем
        scheduled_posts_qset = ScheduledPosts.objects.filter(
            bot_user=bot_user_obj,
            news_post=i_post,
        ).only("when_send", "is_sent")
        if len(scheduled_posts_qset) > 1:
            # Изменяем дату и время отправки для неотправленных постов на "сейчас"
            not_sent_posts = scheduled_posts_qset.filter(is_sent=False)
            not_sent_posts.update(when_send=datetime.datetime.now())
            continue

        # Планируем пост к отправке
        scheduling_post_for_sending(
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
    posts = ScheduledPosts.objects.filter(
        is_sent=False,
        when_send__lte=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
    ).prefetch_related("bot_user").prefetch_related("news_post")

    # Получаем пользователей
    bot_user_ids = set(posts.values_list('bot_user', flat=True))
    bot_users = BotUser.objects.filter(id__in=bot_user_ids).only('id', 'tlg_id')

    # Поочереди достаём посты для конкретного юзера и отправляем их сокращенный вариант
    for i_usr in bot_users:
        selection_hash = hashlib.md5(f'{time_now}{i_usr.tlg_id}'.encode('utf-8')).hexdigest()
        i_usr_posts = posts.filter(bot_user=i_usr)
        i_usr_posts.update(selection_hash=selection_hash)
        posts_str = (f'🗞 <b>Есть новости для Вас</b>\n<i>(по состоянию на {time_now})</i>\n\n\n\n'
                     f'<tg-spoiler>$$$news_collection {selection_hash}</tg-spoiler>')

        # Добавляем id интереса в общий список
        for i_post in i_usr_posts:
            if i_post.interest:     # Бывает, что у поста не указан интерес. Редко, но может быть
                interests_ids.append(i_post.interest.id)

        MY_LOGGER.debug(f'Отправляем уведомление о выходе подборки постов юзеру: {i_usr!r}')
        send_result = send_message_by_bot(chat_id=i_usr.tlg_id, text=posts_str)
        if not send_result:
            MY_LOGGER.warning(f'Не удалось уведомление о выходе подборки постов юзеру: {i_usr!r}')
            continue

        # Обновляем флаг is_sent у запланированных к отправке постов
        i_usr_posts.update(is_sent=True)

    # Обновляем дату и время крайней отправки у интересов
    Interests.objects.filter(id__in=set(interests_ids)).update(
        last_send=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
    )

    MY_LOGGER.info('Конец задачи по формированию подборки постов для пользователей и отправки уведомления в ТГ')
