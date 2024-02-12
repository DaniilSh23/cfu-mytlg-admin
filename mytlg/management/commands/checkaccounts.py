"""
Команда для проверки телеграмм аккаунтов.

Команда получает из БД все незапущенные и незабаненные аккаунты, через указанные у них прокси пробует установить
соединение с сервером телеграмма и выполнить метод get_me().

Так как используется оригинальный объект TelegramClient из библиотеки telethon, то при неудачной проверке может быть
вызвана блокирующая операция с запросом номера телефона или токена бота, которая встроена в telethon.

Обработку неработоспособных аккаунтов необходимо выполнять вручную.

Также при повторном запуске команды, например если столкнулись с неработоспосбным аккаунтом, рекомендуется запустить,
либо временно отметить как забаненный аккаунт, который ранее уже был успешно проверен. Это необходимо, чтобы повторно
не кидать от лица работоспособного аккаунта запросы к телеграмму и не спровоцировать бан.
"""

import asyncio
from telethon.network import connection
import socks
from django.core.management import BaseCommand
from loguru import logger
from telethon import TelegramClient

from mytlg.models import TlgAccounts, Proxys


class Command(BaseCommand):
    live_accounts = []

    def handle(self, *args, **options):
        logger.info('Старт команды для проверки телеграмм аккаунтов')

        accounts = TlgAccounts.objects.filter(is_run=False, banned=False).prefetch_related("proxy")
        for i_acc in accounts:
            logger.info(f'Список аккаунтов: {self.live_accounts}')
            logger.info(f'Аккаунт PK={i_acc.pk} | Проверяем аккаунт.')
            asyncio.run(self.check_accounts_work(account=i_acc, proxy=i_acc.proxy))

        logger.success(f'Проверка завершена! Проверено {len(accounts)} аккаунтов, '
                       f'количество живых аккаунтов: {len(self.live_accounts)}. '
                       f'Cписок живых аккаунтов: {self.live_accounts}')

    async def check_accounts_work(self, account: TlgAccounts, proxy: Proxys):
        """
        Метод для непосредственного запуска аккаунта и выполнения метода get_me().
        """
        proxy_dct = await self.make_proxy_dict(proxy_str=proxy.make_proxy_string())
        tlg_client = TelegramClient(
            session=account.session_file.path,
            api_id=account.json_data.get("app_id"),
            api_hash=account.json_data.get("app_hash"),
            device_model=account.json_data.get("device"),
            app_version=account.json_data.get("app_version", "4.16.30"),
            system_version=account.json_data.get("system_version", "4.16.30-vxCUSTOM"),
            lang_code=account.json_data.get("lang_code", "en"),
            system_lang_code=account.json_data.get("system_lang_code", "en"),
            proxy=proxy_dct,
            use_ipv6=proxy.protocol_type,
            timeout=15,
            connection_retries=5,
        )
        logger.info(f'Аккаунт PK={account.pk} | Пробуем подключиться к серверу Telegram')
        await tlg_client.start()
        logger.debug(f'Аккаунт PK={account.pk} | Проверяем запуск акканута, путём вызова метода get_me()')
        me = await tlg_client.get_me()
        logger.debug(f'Аккаунт PK={account.pk} | Результат метода get_me():\n{me.stringify()}')
        self.live_accounts.append(account.pk)
        return me

    async def make_proxy_dict(self, proxy_str: str) -> dict:
        """
        Функция для преобразования прокси из строки в словарь, который можно подать на вход telethon.
        Прокся в параметре proxy_str приходит в таком виде:
            protocol:host:port:user:password:ipv6
        Например:
            socks5:192.168.10.1:4444:user:passwd:True
        """
        proxy_lst = proxy_str.split(':')
        proxy_dct = {
            'addr': proxy_lst[1],
            'port': int(proxy_lst[2]),
        }

        # Если к проксе указан логин и пароль
        if len(proxy_lst) >= 5:
            proxy_dct['username'] = proxy_lst[3]
            proxy_dct['password'] = proxy_lst[4]

        # Устанавливаем протокол соединения для прокси
        if proxy_lst[0].lower() == 'http':
            proxy_dct['proxy_type'] = connection.ConnectionHttp
        elif proxy_lst[0].lower() == 'https':
            proxy_dct['proxy_type'] = connection.ConnectionHttp
        elif proxy_lst[0].lower() == 'socks4':
            proxy_dct['proxy_type'] = socks.SOCKS4
            proxy_dct['rdns'] = True
        elif proxy_lst[0].lower() == 'socks5':
            proxy_dct['proxy_type'] = socks.SOCKS5
            proxy_dct['rdns'] = True

        return proxy_dct