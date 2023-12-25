from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import TlgAccounts
from mytlg.utils import encoding_file_to_base64
from telegram_accounts.utils import account_json_data_formatter


class TelegramAccountService:
    """
    Сервис для бизнес-логики, связанной с телеграм аккаунтами.
    """

    @staticmethod
    def get_running_accounts():
        """
        Метод для получения аккаунтов, которые должны быть запущены
        """
        MY_LOGGER.debug('Запущен сервис с бизнес-логикой для получения аккаунтов, которые должны быть запущены')
        accounts = (TlgAccounts.objects.filter(is_run=True).only('id', 'json_data').
                    prefetch_related('proxy').
                    prefetch_related('channels'))
        result = []
        for i_acc in accounts:
            result.append({
                'acc_pk': i_acc.pk,
                'acc_json_data': account_json_data_formatter(i_acc.json_data),
                'proxy': i_acc.proxy.make_proxy_string(),
                'channels_ids': [str(i_ch.channel_id) for i_ch in i_acc.channels.all()]
            })

        return {'result': result}

    @staticmethod
    def get_session_file(acc_pk):
        """
        Метод для выполнения бизнес-логики в запросе на получение файла сессии.
        """
        try:
            session_file = TlgAccounts.objects.get(pk=acc_pk).session_file
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не найден файл сессии для аккаунта с PK={acc_pk}')
            return 404, {'result': False, 'description': f'Not found session file for tlg account with PK == {acc_pk}'}

        b64_file = encoding_file_to_base64(file_path=session_file.path)
        return 200, {'result': True, 'file': b64_file}
