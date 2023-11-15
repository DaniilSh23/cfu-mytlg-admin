from mytlg.models import TlgAccounts
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
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

    @staticmethod
    def get_tlgaccounts_that_dont_have_max_channels(max_ch_per_acc):
        acc_qset = (
            TlgAccounts.objects.annotate(num_ch=Count('channels')).filter(num_ch__lt=max_ch_per_acc, is_run=True)
            .only("channels", "acc_tlg_id").prefetch_related("channels"))
        return acc_qset

    @staticmethod
    def exclude_allready_subscripted_channels(excluded_ids):
        accs = TlgAccounts.objects.filter(is_run=True).only('channels').prefetch_related('channels')
        for i_acc in accs:
            excluded_ids.extend([i_ch.id for i_ch in i_acc.channels.all()])
        excluded_ids = list(set(excluded_ids))  # Избавляемся от дублей
        return excluded_ids

    @staticmethod
    def get_tlg_accounts_for_start_or_stop():
        tlg_accounts = TlgAccounts.objects.filter(is_run=True, for_search=False).only("id", "session_file",
                                                                                      "proxy").prefetch_related(
            "proxy")
        return tlg_accounts
