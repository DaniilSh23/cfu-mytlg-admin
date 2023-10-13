from mytlg.models import TlgAccounts
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


class TlgAccountsService:

    @staticmethod
    def filter_and_update_tlg_account(pk, dct):
        return TlgAccounts.objects.filter(pk=pk).update(**dct)

    @staticmethod
    def get_tlg_account_by_pk(acc_pk):
        try:
            return TlgAccounts.objects.get(pk=int(acc_pk))
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Запрошены для несуществующий аккаунт (PK аккаунта == {acc_pk!r}')
            return None

    @staticmethod
    def get_tlg_account_only_id_by_pk(pk):
        try:
            return TlgAccounts.objects.only("id").get(pk=pk)
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Аккаунт с PK == {pk!r} не найден в БД.')
            return None
