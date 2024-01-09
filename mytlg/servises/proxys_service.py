from mytlg.models import Proxys


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
            is_checked=proxy_data.get('is_checked'),
            last_check=proxy_data.get('last_check'),
        ).save()
        return proxy

    @staticmethod
    def delete_proxy(proxy_id):
        Proxys.objects.get()
