from mytlg.models import Channels
from django.db.models import QuerySet
from django.db import transaction
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
    def get_tlg_account_channels_list(tlg_account) -> QuerySet | list:
        try:
            return tlg_account.channels.all()
        except Exception as e:
            MY_LOGGER.warning(f'Запрошены каналы не найдены для аккаунта (PK аккаунта == {tlg_account!r} \n '
                              f'Ошибка: {e}')
            return []

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

    @staticmethod
    def update_or_create(channel_link, defaults):
        ch_obj, ch_created = Channels.objects.update_or_create(channel_link=channel_link, defaults=defaults)
        return ch_obj, ch_created

    @staticmethod
    def update_or_create_channels_from_data_file(i_data, theme_obj):
        for i_key, i_val in i_data.items():
            # ch_obj, ch_created = Channels.objects.update_or_create(
            ch_obj, ch_created = ChannelsService.update_or_create(
                channel_link=i_val[1],
                defaults={
                    "channel_name": i_key,
                    "channel_link": i_val[1],
                    "subscribers_numb": int(i_val[0]),
                    "theme": theme_obj,
                }
            )
            MY_LOGGER.debug(f'Канал {ch_obj} был {"создан" if ch_created else "обновлён"}!')

    @staticmethod
    def process_tlg_channels(ser):
        ch_ids_lst = [int(i_ch.get("ch_pk")) for i_ch in ser.data.get('channels')]
        ch_qset = Channels.objects.filter(id__in=ch_ids_lst)
        for i_ch in ch_qset:
            for j_ch in ser.data.get('channels'):
                if int(j_ch.get("ch_pk")) == i_ch.pk:
                    new_ch_data = j_ch
                    break
            else:
                MY_LOGGER.warning(f'В запросе не приходила инфа по каналу с PK=={i_ch.pk!r}')
                ch_ids_lst.remove(i_ch.pk)
                continue
            i_ch.channel_id = new_ch_data.get('ch_id')
            i_ch.channel_name = new_ch_data.get('ch_name')
            i_ch.subscribers_numb = new_ch_data.get('subscribers_numb')
            i_ch.is_ready = True
        MY_LOGGER.debug('Выполняем в транзакции 2 запроса: обновление каналов, привязка к ним акка tlg')
        return ch_ids_lst, ch_qset

    @staticmethod
    def bulk_update_channels(ch_ids_lst, ch_qset, tlg_acc_obj):
        with transaction.atomic():
            Channels.objects.bulk_update(ch_qset,
                                         fields=["channel_id", "channel_name", "subscribers_numb", "is_ready"])
            tlg_acc_obj.channels.add(*ch_ids_lst)
