from mytlg.models import BotSettings
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


class BotSettingsService:

    @staticmethod
    def get_bot_settings_by_key(key: str) -> str | None:
        try:
            return BotSettings.objects.get(key=key).value
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Настройка бота не найдена (Имя настройки key == {key}')
            return None
