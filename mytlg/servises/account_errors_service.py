from mytlg.models import AccountsErrors
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


class TlgAccountErrorService:

    @staticmethod
    def create_tlg_account_error(ser, tlg_acc):
        AccountsErrors.objects.create(
            error_type=ser.validated_data.get("error_type"),
            error_description=ser.validated_data.get("error_description"),
            account=tlg_acc,
        )
