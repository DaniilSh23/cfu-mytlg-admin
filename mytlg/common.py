import csv
import json
from io import TextIOWrapper

from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import Channels, Categories, NewsPosts, Interests, BotSettings, BotUser, ScheduledPosts, BlackLists
from mytlg.utils import calculate_sending_datetime


def save_json_channels(file, encoding):  # TODO: переписать
    """
    Функция, которая отвечает за создание каналов в админке из JSON файла
    :return:
    """
    # Обрабатываем загруженный csv файл
    json_file = TextIOWrapper(
        file,
        encoding=encoding,
    )
    json_data = json.loads(json_file.read())
    category = json_data.get("category")
    category, created = Categories.objects.get_or_create(
        category_name=category.lower(),
        defaults={
            "category_name": category.lower(),
        }
    )
    MY_LOGGER.debug(f'Категория каналов {category.category_name!r} была {"создана" if created else "получена"}.')

    channels_data = json_data.get("data")
    channels_links = []
    for i_ch_name, i_ch_data in channels_data.items():
        channels_links.append(i_ch_data[1])
    channels_in_db_qset = Channels.objects.filter(channel_link__in=channels_links).only('channel_link')
    channels_in_db_links = [i_ch_in_db.channel_link for i_ch_in_db in channels_in_db_qset]

    channels = []
    for i_ch_name, i_ch_data in channels_data.items():
        if i_ch_data[1] not in channels_in_db_links:
            channels.append(Channels(
                channel_name=i_ch_name,
                channel_link=i_ch_data[1],
                category=category,
                subscribers_numb=i_ch_data[0],
            ))

    Channels.objects.bulk_create(channels)
    MY_LOGGER.debug(f'Каналы загружены в БД.')

    return channels


def scheduling_post_for_sending(post: NewsPosts):
    """
    Отбор пользователей для поста.
    """
    MY_LOGGER.debug(f'Планируем пост к отправке.')

    users_qset = BotUser.objects.all().only('id')
    for i_user in users_qset:

        # Проверяем на предмет соответствия черному списку
        black_lst_qset = BlackLists.objects.filter(bot_user=i_user)
        if len(black_lst_qset) > 0:
            black_check_rslt = black_list_check(news_post=post, black_list=black_lst_qset[0])
            if not black_check_rslt:
                MY_LOGGER.warning(f'Пост {post!r} не прошёл черный список юзера {i_user!r}')
                continue

        interests = (
            Interests.objects.filter(category=post.channel.category, bot_user=i_user, is_active=True,
                                     interest_type='main')
            .only('id', 'interest', 'embedding', 'when_send')
        )
        if len(interests) < 1:
            MY_LOGGER.warning(f'У юзера PK=={i_user.pk} не указаны интересы')
            continue
        interest_lst = [
            (i_interest.interest, [float(i_emb) for i_emb in i_interest.embedding.split()])
            for i_interest in interests
        ]

        # Пилим индексную базу из эмбеддингов для интересов
        embeddings = OpenAIEmbeddings()
        index_db = FAISS.from_embeddings(text_embeddings=interest_lst, embedding=embeddings)

        # Находим релевантные куски подав на вход эмбеддинги
        relevant_pieces = index_db.similarity_search_with_score_by_vector(
            embedding=[float(i_emb) for i_emb in post.embedding.split()],
            k=1,
        )

        # Фильтруем по векторному расстоянию подходящие куски
        similarity_index_for_interests = float(BotSettings.objects.get(key='similarity_index_for_interests').value)
        filtered_rel_pieces = list(filter(lambda piece: piece[1] < similarity_index_for_interests, relevant_pieces))

        if len(filtered_rel_pieces) < 1:  # Выходим, если куски очень далеки от схожести
            MY_LOGGER.warning(f'У юзера PK=={i_user.pk} нет релевантных интересов для поста с PK=={post.pk}')
            continue

        sending_datetime = None
        interest = interests[0]
        for i_interest in interests:
            if filtered_rel_pieces[0][0].page_content == i_interest.interest:
                MY_LOGGER.debug(f'Найден релевантный интерес у юзера {i_user.pk!r}')
                # Рассчитываем время предстоящей отправки
                sending_datetime = calculate_sending_datetime(
                    last_send=i_interest.last_send,
                    send_period=i_interest.send_period,
                    when_send=i_interest.when_send,
                )
                interest = i_interest
                break

        # Создаём запись в таблице спланированных постов
        ScheduledPosts.objects.create(
            bot_user=i_user,
            news_post=post,
            when_send=sending_datetime,
            interest=interest,
        )


def black_list_check(news_post: NewsPosts, black_list: BlackLists) -> bool:
    """
    Функция для проверки поста на предмет соответствия черному списку.
    Проверяет вхождение ключевых слов в:
        - ссылке на канал
        - названии канала
        - описании канала
        - тексте поста из канала
    Возвращает:
        False - найдено вхождение ключевых слов из черного списка, пост надо откинуть
        True - пост успешно прошёл черный список и может быть обработан далее
    """
    MY_LOGGER.debug(f'Вызвана функция для проверки поста на соответствие черному списку {black_list}')
    check_rslt = True

    # Достаём нужную инфу
    black_keywords_lst = black_list.keywords.split('\n')
    channel_link = news_post.channel.channel_link.lower()
    channel_name = news_post.channel.channel_name.lower()
    channel_description = news_post.channel.description.lower()
    post_text = news_post.text.lower()

    # Ищем вхождение ключевых слов
    for i_word in black_keywords_lst:
        for i_step in (channel_link, channel_name, channel_description, post_text):
            if i_word.lower() in i_step:
                MY_LOGGER.warning(f'Найдено вхождение ключевого слова {i_word.lower()!r} в {i_step}. '
                                  f'Пост должен быть откинут!')
                check_rslt = False
                break
    if check_rslt:
        MY_LOGGER.success(f'Черный список пройден успешно!')
    return check_rslt
