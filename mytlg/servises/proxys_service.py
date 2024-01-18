from mytlg.models import Proxys
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.servises.tlg_accounts_service import TlgAccountsService
from mytlg.servises.bot_settings_service import BotSettingsService
from mytlg.servises.proxy_providers_service import AsocksProxyService
import time


class ProxysService:

    @staticmethod
    def create_proxy(proxy_data: dict) -> Proxys | bool:
        try:
            MY_LOGGER.info(f'Создаем прокси: {proxy_data}')
            proxy = Proxys(
                country_code=proxy_data.get('country_code'),
                description=proxy_data.get('description'),
                external_proxy_id=proxy_data.get('external_proxy_id'),
                protocol=proxy_data.get('protocol', 'socks5'),
                protocol_type=proxy_data.get('protocol_type', False),
                host=proxy_data.get('host'),
                port=proxy_data.get('port'),
                username=proxy_data.get('login'),
                password=proxy_data.get('password'),
            )
            proxy.save()
            return proxy
        except Exception as e:
            MY_LOGGER.warning(f'Ошибка при сохранении прокси {proxy_data} в базу данных {e}')
            return False

    @staticmethod
    def get_proxy_by_id(proxy_id):
        try:
            proxy = Proxys.objects.get(proxy_id=proxy_id)
            return proxy
        except ObjectDoesNotExist as e:
            MY_LOGGER.warning(f'Ошибка при получении прокси с id: {proxy_id}. Ошибка: {e}')

    @staticmethod
    def delete_proxy(proxy_pk):
        try:
            Proxys.objects.get(pk=proxy_pk).delete()
        except Exception as e:
            MY_LOGGER.warning(f'Не удалось удалить прокси с id: {proxy_pk}. Ошибка: {e}')

    @staticmethod
    def get_all_free_proxys():
        free_proxys = Proxys.objects.exclude(tlgaccounts__isnull=False)
        return free_proxys

    @staticmethod
    def get_free_proxy_by_country_code(country_code):
        free_proxy = Proxys.objects.filter(tlgaccounts__isnull=True, country_code=country_code).first()
        return free_proxy

    @staticmethod
    def fill_proxys_reserve():
        reserve_proxy_quantity_per_account = int(
            BotSettingsService.get_bot_settings_by_key('rezerv_proxy_quantity_per_account'))
        free_proxy = ProxysService.get_all_free_proxys().count()
        tlg_accounts = TlgAccountsService.get_running_accounts()
        required_proxy_quantity = tlg_accounts.counts() * reserve_proxy_quantity_per_account
        if free_proxy < required_proxy_quantity:
            ProxysService.create_reserve_proxys(free_proxy, required_proxy_quantity)

    @staticmethod
    def create_reserve_proxys(free_proxy, required_proxy_quantity):
        count_proxy_to_create = required_proxy_quantity - free_proxy
        for _ in range(count_proxy_to_create):
            proxy_data = AsocksProxyService.get_new_proxy_by_country_code(country_code='CU')
            ProxysService.create_proxy(proxy_data)
            time.sleep(5)
