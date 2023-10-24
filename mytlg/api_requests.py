"""
Запросы к другим сервисам.
"""

import requests

from cfu_mytlg_admin.settings import ACCOUNT_SERVICE_HOST, MY_LOGGER


def post_req_to_accounts_service_for_start_subscription(req_data):
    """
    POST запрос к сервису управления аккаунтами для старта подписки на каналы.
    """
    MY_LOGGER.debug(f'Выполняем запрос к сервису управления аккаунтами для старта подписки | '
                    f'Данные запроса:\n{req_data}')
    response = requests.post(url=ACCOUNT_SERVICE_HOST, json=req_data)
    if response.status_code != 200:
        MY_LOGGER.warning(f'Неудачный запрос к сервису управления аккаунтами для старта подписки на каналы. | '
                          f'Ответ: {response.text}')
        return False, response.text
    MY_LOGGER.success('Успешный запрос к сервису управления аккаунтами для старта подписки на каналы.')
    return True, response.text
