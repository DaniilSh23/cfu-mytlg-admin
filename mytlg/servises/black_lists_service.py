from mytlg.models import BlackLists
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


class BlackListsService:

    @staticmethod
    def update_or_create(tlg_id, defaults):
        obj, created = BlackLists.objects.update_or_create(bot_user__tlg_id=tlg_id, defaults=defaults)
        return obj, created

    @staticmethod
    def get_channel_by_pk(pk: int) -> BlackLists | None:
        try:
            return BlackLists.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return None
