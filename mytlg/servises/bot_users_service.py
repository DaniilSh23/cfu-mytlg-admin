from mytlg.models import BotUser
from django.core.exceptions import ObjectDoesNotExist


class BotUsersService:

    @staticmethod
    def get_bot_user_by_tg_id(tlg_id: int) -> BotUser | None:
        try:
            return BotUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            return

    @staticmethod
    def update_or_create_bot_user(tlg_id: str, defaults: dict) -> tuple:
        bot_usr_obj, created = BotUser.objects.update_or_create(tlg_id, defaults)
        return bot_usr_obj, created

