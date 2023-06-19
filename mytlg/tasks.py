import asyncio
import csv
import datetime
import io
import os

import pytz
from celery import shared_task

from cfu_mytlg_admin.settings import MY_LOGGER, TIME_ZONE, BASE_DIR


# В ивент лупе нельзя кидать запросы к БД, поэтому собираем всю инфу об отправке в этот словарик
# и после из него берём инфу для записи в таблицу рассылок.
# В словаре такой формат: {user_id: {send_status: str, send_datetime: datetime}}
SEND_RESULT = dict()


@shared_task
def scheduled_task_example():
    """
    Пример отложенной задачи, которая печатает в консоль.
    """
    print(f'Привет мир, я отложенная задача. Сейчас: {datetime.datetime.utcnow()}')
