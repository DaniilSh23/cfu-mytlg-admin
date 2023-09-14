from django.core.management import BaseCommand
from loguru import logger

from mytlg.models import BotSettings


class Command(BaseCommand):
    """
    Команда для по установки настроек
    """
    def handle(self, *args, **options):
        logger.info('Старт команды по установке настроек')
        keys = {
            'bot_admins': '1978587604',
            'max_channels_per_acc': '45',
        }
        for i_key, i_val in keys.items():
            _, i_created = BotSettings.objects.update_or_create(
                key=i_key,
                defaults={'key': i_key, 'value': i_val}
            )
            logger.success(f'Ключ {i_key} успешно {"создан" if i_created else "обновлён"} со значением {i_val}')

        logger.info('Окончание команды по установке настроек')