from mytlg.models import BlackLists
from django.core.exceptions import ObjectDoesNotExist


class BlackListsService:

    @staticmethod
    def update_or_create(tlg_id, defaults):
        obj, created = BlackLists.objects.update_or_create(bot_user__tlg_id=tlg_id, defaults=defaults)
        return obj, created

    @staticmethod
    def get_blacklist_by_bot_user_tlg_id(tlg_id: int):
        try:
            return BlackLists.objects.get(bot_user__tlg_id=tlg_id)
        except ObjectDoesNotExist as e:
            raise ObjectDoesNotExist from e
