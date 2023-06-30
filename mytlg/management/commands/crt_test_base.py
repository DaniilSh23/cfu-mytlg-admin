from django.core.management import BaseCommand
from loguru import logger

from mytlg.models import Themes, Channels


class Command(BaseCommand):
    """
    Команда для наполнения БД тестовыми данными (категории и каналы)
    """
    def handle(self, *args, **options):
        logger.info('Старт команды по наполнению БД тестовыми данными (категории и каналы)!')

        for i_val in range(50):
            i_theme, i_created = Themes.objects.get_or_create(
                theme_name=f'test_theme_{i_val}',
                defaults={'theme_name': f'test_theme_{i_val}'}
            )
            logger.success(f'Тема "test_theme_{i_val}" {"создана" if i_created else "уже есть"} в БД.')
            for j_val in range(19):
                ch_obj, j_created = Channels.objects.get_or_create(
                    channel_link=j_val,
                    defaults={
                        "channel_name": f'test_channel_name_{j_val}',
                        "channel_link": f'test_channel_link_{j_val}',
                        "theme": i_theme
                    }
                )
                logger.success(f'Канал "test_channel_link_{j_val}" {"создан" if j_created else "уже есть"} в БД.')

        logger.info('Окончание команды по наполнению БД тестовыми данными (категории и каналы)!')
