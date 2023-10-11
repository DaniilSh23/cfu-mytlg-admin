from mytlg.models import Channels
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist


class ChannelsService:

    @staticmethod
    def check_selected_channels(selected_channels_lst: list) -> list:
        return list(map(lambda i_ch: i_ch.isdigit(), selected_channels_lst))

    @staticmethod
    def get_channels_qset_by_list_of_ids(selected_channels_lst: list) -> QuerySet:
        return Channels.objects.filter(pk__in=selected_channels_lst)

    @staticmethod
    def get_channel_by_pk(pk: int) -> Channels | None:
        try:
            return Channels.objects.get(pk)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def filter_channel_by_category(category):
        return Channels.objects.filter(category).only("id")
