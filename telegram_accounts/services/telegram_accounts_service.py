from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import TlgAccounts
from mytlg.utils import encoding_file_to_base64


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
        accounts = (TlgAccounts.objects.filter(is_run=True, for_search=True).only('id', 'acc_tlg_id').prefetch_related(
            'proxy').
                    prefetch_related('channels'))
        result = []
        for i_acc in accounts:
            result.append({
                'pk': i_acc.pk,
                'tlg_id': i_acc.acc_tlg_id,
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
