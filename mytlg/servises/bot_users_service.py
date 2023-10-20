from mytlg.models import BotUser
from django.core.exceptions import ObjectDoesNotExist


class BotUsersService:

    @staticmethod
    def get_bot_user_by_tg_id(tlg_id: int) -> BotUser | None:
        try:
            return BotUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def update_or_create_bot_user(tlg_id: str, defaults_dict: dict) -> tuple:
        bot_usr_obj, created = BotUser.objects.update_or_create(tlg_id=tlg_id, defaults=defaults_dict)
        return bot_usr_obj, created

    @staticmethod
    def get_all_bot_users_ids():
        return BotUser.objects.all().only('id')

    @staticmethod
    def get_users_queryset_for_scheduling_post(bot_usr):
        if not bot_usr:
            users_qset = BotUsersService.get_all_bot_users_ids()
        else:
            users_qset = (bot_usr,)  # Сделал из одного элемента кортеж, чтобы можно было итерироваться
        return users_qset

    @staticmethod
    def clear_bot_users_category_and_channels(tlg_id):
        bot_usr = BotUser.objects.get(tlg_id=tlg_id)
        bot_usr.category.clear()
        bot_usr.channels.clear()
        return bot_usr
