"""
Сервис для бизнес-логики, связанной с кастомными каналами пользователей.
"""
import datetime

from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import BotUser
from user_interface.models import CustomChannelsSettings


class CustomChannelsService:

    @staticmethod
    def update_or_create_custom_channels_settings(tlg_id: str, when_send: datetime, send_period: str,
                                                  only_custom_channels: bool | None):
        """
        Обновляем или создаем настройки для постов из кастомных каналов пользователей.
        """
        try:
            bot_user = BotUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist as err:
            MY_LOGGER.warning(f'Не найден объъект BotUser с tlg_id=={tlg_id} | Ошибка: {err}')
            return
        bot_user.only_custom_channels = only_custom_channels if only_custom_channels else False
        bot_user.save()
        MY_LOGGER.debug(f'Значение bot_user.only_custom_channels == {bot_user.only_custom_channels}')
        obj, created = CustomChannelsSettings.objects.update_or_create(
            bot_user=bot_user,
            defaults={
                "bot_user": bot_user,
                "when_send": when_send,
                "send_period": send_period,
                "last_send": datetime.datetime.now(),
            }
        )
        MY_LOGGER.debug(f'Запись CustomChannelsSettings для юзера tlg_id=={tlg_id} успешно '
                        f'{"создана" if created else "обновлена"}.')
        return obj
