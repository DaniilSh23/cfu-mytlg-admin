from mytlg.models import Channels
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from cfu_mytlg_admin.settings import MY_LOGGER


class ChannelsService:

    @staticmethod
    def check_selected_channels(selected_channels_lst: list) -> list:
        return list(map(lambda i_ch: i_ch.isdigit(), selected_channels_lst))

    @staticmethod
    def get_channels_qset_by_list_of_ids(selected_channels_lst: list) -> QuerySet:
        return Channels.objects.filter(pk__in=selected_channels_lst)

    @staticmethod
    def get_tlg_account_channels_list(tlg_account) -> QuerySet | None:
        try:
            return tlg_account.channels.all()
        except Exception as e:
            MY_LOGGER.warning(f'Запрошены каналы не найдены для аккаунта (PK аккаунта == {tlg_account!r} \n '
                              f'Ошибка: {e}')
            return None

    @staticmethod
    def get_channel_by_pk(pk: int) -> Channels | None:
        try:
            return Channels.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def filter_channel_by_category(category):
        return Channels.objects.filter(category).only("id")

    @staticmethod
    def create_and_process_channels_lst(acc_pk, channels_qset):
        channels_lst = []
        for i_channel in channels_qset:
            # Достаём из БД список других аккаунтов, с которым связан каждый канал
            acc_lst = i_channel.tlg_accounts.all().exclude(Q(pk=int(acc_pk)))
            discard_channel = False  # Флаг "отбросить канал"
            for i_acc in acc_lst:
                if i_acc.is_run:  # Если другой аккаунт уже запущен и слушает данный канал
                    discard_channel = True  # Поднимаем флаг
                    break
            if not discard_channel:  # Если флаг опущен
                # Записываем данные о канале в список
                channels_lst.append(
                    {
                        "pk": i_channel.pk,
                        "channel_id": i_channel.channel_id,
                        "channel_name": i_channel.channel_name,
                        "channel_link": i_channel.channel_link,
                    }
                )
        return channels_lst

    @staticmethod
    def get_channels_qset_only_ids(theme_obj):
        try:
            return Channels.objects.filter(category=theme_obj).only("id")
        except Exception as e:
            MY_LOGGER.warning(f'Запрошены каналы не найдены для категории (Категории == {theme_obj!r} \n '
                              f'Ошибка: {e}')
            return None

