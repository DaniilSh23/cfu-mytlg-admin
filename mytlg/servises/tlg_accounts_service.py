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
        tlg_accounts = TlgAccounts.objects.filter(is_run=True).only("id", "session_file",
                                                                    "proxy").prefetch_related(
            "proxy")
        return tlg_accounts

    @staticmethod
    def get_tlg_account_id_for_search_custom_channels():
        tlg_accounts = TlgAccounts.objects.filter(for_search=True).only("id")
        if tlg_accounts:
            tlg_account_id = tlg_accounts[0].id
            MY_LOGGER.info(f'Найден телеграм аккаунт с PK == {tlg_account_id} для использования при поиске каналов.')
        else:
            tlg_account_id = None
            MY_LOGGER.warning('Не найден телеграм аккаунт для использования при поиске каналов')
        return tlg_account_id

    @staticmethod
    def get_tlg_account_by_channel(channel):
        return TlgAccounts.objects.filter(channels__id=channel.channel_id).first()

    @staticmethod
    def get_tlg_account_for_subscribe_custom_channels(max_channels_per_acc, channels_count):
        # TODO написать правильную логику для отбора нужного аккаунта
        accounts = TlgAccounts.objects.filter(is_run=True, for_search=False)

        for account in accounts:
            if account.num_ch - channels_count < max_channels_per_acc:
                MY_LOGGER.info(f'Выбран аккаунт для подписки на кастомные каналы {account}')
                return account
            else:
                MY_LOGGER.info('Не найден аккаунт для подписки на кастомные каналы')
