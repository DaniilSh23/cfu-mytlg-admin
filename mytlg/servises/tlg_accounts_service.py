from mytlg.models import TlgAccounts


class TlgAccountsService:

    @staticmethod
    def filter_and_update_tlg_account(pk, dct):
        return TlgAccounts.objects.filter(pk=pk).update(**dct)


