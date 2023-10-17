from mytlg.models import AccountsErrors
from cfu_mytlg_admin.settings import MY_LOGGER


class TlgAccountErrorService:

    @staticmethod
    def create_tlg_account_error(ser, tlg_acc):
        try:
            error = AccountsErrors.objects.create(
                error_type=ser.validated_data.get("error_type"),
                error_description=ser.validated_data.get("error_description"),
                account=tlg_acc,
            )
            MY_LOGGER.info(
                f'Создана ошибка телеграм аккаунта {tlg_acc}, тип ошибки {error.error_type}, '
                f'описание ошибки {error.error_description}')
        except Exception as e:
            MY_LOGGER.error(f'Не удалось создать ошибку телеграм аккаунта {tlg_acc}: {e}')
