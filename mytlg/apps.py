from django.apps import AppConfig


class MytlgConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mytlg'
    verbose_name = 'Мой телеграм'

    def ready(self):
        """
        Этот метод унаследован от AppConfig. В нём можно написать ту логику,
        которую хотим выполнить при запуске Django.
        """
        ...
