"""
Сервис для бизнес-логики, связанной с кастомными каналами пользователей.
"""
import datetime

from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import CustomChannelsSettings, BotUser


class CustomChannelsService:

    @staticmethod
    def update_or_create_custom_channels_settings(tlg_id: str, when_send: datetime, send_period: str):
        """
        Обновляем или создаем настройки для постов из кастомных каналов пользователей.
        """
        try:
            bot_user = BotUser.objects.get(tlg_id=int(tlg_id))
        except ObjectDoesNotExist as err:
            MY_LOGGER.warning(f'Не найден объъект BotUser с tlg_id=={tlg_id} | Ошибка: {err}')
            return

        obj, created = CustomChannelsSettings.objects.update_or_create(
            bot_user=bot_user,
            defaults={
                "when_send": when_send,
                "send_period": send_period,
            }
        )
        MY_LOGGER.debug(f'Запись CustomChannelsSettings для юзера tlg_id=={tlg_id} успешно '
                        f'{"создана" if created else "обновлена"}.')
        return obj