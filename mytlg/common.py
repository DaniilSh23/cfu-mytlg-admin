import csv
import json
from io import TextIOWrapper

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import Channels, Categories


def save_json_channels(file, encoding):     # TODO: переписать
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
