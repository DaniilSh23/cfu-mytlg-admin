from mytlg.models import Proxys
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


class ProxysService:

    @staticmethod
    def create_proxy(proxy_data: dict) -> Proxys:
        proxy = Proxys(
            description=proxy_data.get('description'),
            protocol_type=proxy_data.get('protocol_type'),
            protocol=proxy_data.get('protocol'),
            host=proxy_data.get('host'),
            port=proxy_data.get('port'),
            username=proxy_data.get('username'),
            password=proxy_data.get('password'),
            # is_checked=proxy_data.get('is_checked'),
            # last_check=proxy_data.get('last_check'),
        ).save()
        return proxy

    @staticmethod
    def get_proxy_by_id(proxy_id):
        try:
            proxy = Proxys.objects.get(proxy_id=proxy_id)
            return proxy
        except ObjectDoesNotExist as e:
            MY_LOGGER.warning(f'Ошибка при получении прокси с id: {proxy_id}. Ошибка: {e}')

    @staticmethod
    def delete_proxy(proxy_id):
        try:
            Proxys.objects.get(id=proxy_id).delete()
        except Exception as e:
            MY_LOGGER.warning(f'Не удалось удалить прокси с id: {proxy_id}. Ошибка: {e}')
