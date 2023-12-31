import csv
import json
from io import TextIOWrapper

from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import Channels, Categories, NewsPosts, Interests, BotSettings, BotUser, ScheduledPosts
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
        for i_interest in interests:
            if filtered_rel_pieces[0][0].page_content == i_interest.interest:
                MY_LOGGER.debug(f'Найден релевантный интерес у юзера {i_user.pk!r}')
                # Рассчитываем время предстоящей отправки
                sending_datetime = calculate_sending_datetime(
                    last_send=i_interest.last_send,
                    send_period=i_interest.send_period,
                    when_send=i_interest.when_send,
                )
                break

        # Создаём запись в таблице спланированных постов
        ScheduledPosts.objects.create(
            bot_user=i_user,
            news_post=post,
            when_send=sending_datetime,
        )
