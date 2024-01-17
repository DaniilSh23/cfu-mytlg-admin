from mytlg.models import Proxys
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


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

