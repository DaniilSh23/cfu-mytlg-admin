import time
from abc import ABC, abstractmethod
import requests

from mytlg.servises.bot_settings_service import BotSettingsService
from cfu_mytlg_admin.settings import MY_LOGGER


class ProxyProviderService(ABC):

    @staticmethod
    @abstractmethod
    def get_new_proxy_by_country_code(country_code):
        pass

    @staticmethod
    @abstractmethod
    def delete_proxy(external_proxy_id):
        pass


class AsocksProxyService(ProxyProviderService):
    service_name = 'Asocks'
    api_key = BotSettingsService.get_bot_settings_by_key('asocks_api_key')
    base_api_url = 'https://api.asocks.com/v2/proxy/'

    @staticmethod
    def get_new_proxy_by_country_code(country_code):
        proxy = AsocksProxyService._create_proxy_port(country_code)
        if proxy:
            return proxy

    @staticmethod
    def delete_proxy(external_proxy_id):
        AsocksProxyService._delete_proxy_port(external_proxy_id)

    @staticmethod
    def _create_proxy_port(country_code, connection_type_id=3, auth_type_id=3, proxy_type_id=3):
        """
        Приватный Метод для создания прокси на сервисе asocks.com
        :param country_code: символьный код страны
        :param connection_type_id: тип соединения для мобильных прокси - 3
        :param auth_type_id: тип авторизации для мобильных прокси - 3
        :param proxy_type_id: тип прокси для мобильных прокси - 3
        :return: словарь с данными для прокси
        """
        url = f'{AsocksProxyService.base_api_url}create-port?apikey={AsocksProxyService.api_key}'
        data = {
            'country_code': country_code,
            'connection_type_id': connection_type_id,
            'auth_type_id': auth_type_id,
            'proxy_type_id': proxy_type_id
        }
        response = requests.post(url=url, json=data)
        if response.status_code != 200:
            MY_LOGGER.warning(f'Ошибка при создании новой прокси на сервисе {AsocksProxyService.service_name}, '
                              f'данные запроса: {data}\n '
                              f'{response.json()}')
            return
        response_data = response.json()
        MY_LOGGER.info(f'Результат запроса к сервису {AsocksProxyService.service_name}: {response_data}')
        if response_data.get('success'):
            data = response_data.get('data')
            proxy_dict = {
                'country_code': data.get('country_code'),
                'login': data.get('login'),
                'password': data.get('password'),
                'host': data.get('server'),
                'port': data.get('port'),
                'protocol': data.get('protocol', 'socks5'),
                'description': f"Прокси-{data.get('country_code')}-{data.get('id')}",
                'external_proxy_id': data.get('id'),
            }
        time.sleep(5)
        return proxy_dict

    @staticmethod
    def _delete_proxy_port(external_proxy_id):
        """
        Метод для удаления прокси на сервисе asocks.com
        :param external_proxy_id:
        :return:
        """
        url = f'{AsocksProxyService.base_api_url}delete-port?apikey={AsocksProxyService.api_key}'
        data = {
            'id': int(external_proxy_id),
        }
        response = requests.post(url=url, json=data)
        if response.status_code != 200:
            MY_LOGGER.warning(f'Ошибка при создании удалении прокси на сервисе {AsocksProxyService.service_name}, '
                              f'данные запроса: {data}\n '
                              f'{response.json()}')
            return
        response_data = response.json()
        MY_LOGGER.info(f'Результат запроса к сервису {AsocksProxyService.service_name}: {response_data}')
        if response_data.get('success'):
            MY_LOGGER.info(f'Прокси порт с id {external_proxy_id} удален')

#print(AsocksProxyService.get_new_proxy_by_country_code(country_code='CU'))
# {'success': True, 'data': {'id': 9360033, 'unique_type': None, 'country_id': 3562981, 'state_id': None, 'city_id': None, 'country_code': 'CU', 'state': None, 'city': None, 'asn': None, 'connection_type_id': 2, 'auth_type_id': 2, 'proxy_type_id': 2, 'status': 'active', 'login': '9360033-all-country-CU', 'password': '2ro3dxib82', 'name': '29 December 10-19 - Cuba', 'created_at': '2023-12-29T10:19:50.000000Z', 'updated_at': None, 'archive_at': None, 'buy_at': None, 'suspended_at': None, 'last_connected_at': None, 'old_server_port_id': None, 'migrated_at': None, 'server': '190.2.151.110', 'port': 11626, 'country': 'Cuba', 'last_connected_ago': 0, 'spent_money_today': None, 'spent_traffic_today': None, 'spent_traffic_yesterday': None, 'spent_traffic_month': None, 'spent_money_month': None, 'isFavorite': 0, 'expires_at': '2024-01-21T09:25:16.000000Z', 'expires_soon': False, 'refresh_link': 'https://api.asocks.com/refresh/-all-country-CU/2ro3dxib82', 'type_id': 2}}
