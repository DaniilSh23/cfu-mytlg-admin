import os
import shutil

from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from cfu_mytlg_admin import settings
from cfu_mytlg_admin.settings import MY_LOGGER

from mytlg.utils import send_command_to_bot


class BotUser(models.Model):
    """
    Модель для юзеров бота
    """
    tlg_id = models.CharField(verbose_name='tlg_id', max_length=30, db_index=True)
    tlg_username = models.CharField(verbose_name='username', max_length=100, blank=False, null=True)
    start_bot_at = models.DateTimeField(verbose_name='первый старт', auto_now_add=True)
    themes = models.ManyToManyField(verbose_name='темы', related_name='bot_user', to='Themes', blank=True)
    sub_themes = models.ManyToManyField(verbose_name='подтемы', related_name='bot_user', to='SubThemes', blank=True)
    channels = models.ManyToManyField(verbose_name='каналы', related_name='bot_user', to='Channels', blank=True)
    when_send_news = models.TimeField(verbose_name='когда присылать новости', blank=False, null=True)

    def __str__(self):
        return f'User TG_ID {self.tlg_id}'

    class Meta:
        ordering = ['-start_bot_at']
        verbose_name = 'юзер бота'
        verbose_name_plural = 'юзеры бота'


class BotSettings(models.Model):
    """
    Настройки бота.
    """
    key = models.CharField(verbose_name='ключ', max_length=50)
    value = models.TextField(verbose_name='значение', max_length=500)

    class Meta:
        ordering = ['-id']
        verbose_name = 'настройка бота'
        verbose_name_plural = 'настройки бота'


class Themes(models.Model):
    """
    Модель для таблицы с темами каналов.
    """
    theme_name = models.CharField(verbose_name='имя темы', max_length=200)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)

    def __str__(self):
        return self.theme_name

    class Meta:
        ordering = ['id']
        verbose_name = 'тема'
        verbose_name_plural = 'темы'


class SubThemes(models.Model):
    """
    Модель для таблицы с подтемами каналов
    """
    sub_theme_name = models.CharField(verbose_name='имя подтмемы', max_length=200)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)

    def __str__(self):
        return self.sub_theme_name

    class Meta:
        ordering = ['id']
        verbose_name = 'подтема'
        verbose_name_plural = 'подтемы'


class Channels(models.Model):
    """
    Модель для таблицы с каналами к каждой тематике
    """
    channel_id = models.CharField(verbose_name='ID канала', max_length=50, blank=True, null=False)
    channel_name = models.CharField(verbose_name='название канала', max_length=150)
    channel_link = models.URLField(verbose_name='ссылка на канал', max_length=150)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)
    theme = models.ForeignKey(verbose_name='тема канала', to=Themes, on_delete=models.CASCADE, blank=False, null=True)
    sub_theme = models.ForeignKey(verbose_name='подтема канала', to=SubThemes, on_delete=models.CASCADE, blank=False, null=True)

    def __str__(self):
        return self.channel_link

    class Meta:
        ordering = ['-id']
        verbose_name = 'канал'
        verbose_name_plural = 'каналы'


class ThemesWeight(models.Model):
    """
    'Вес' темы или подтемы для каждого пользователя
    """
    bot_user = models.ForeignKey(verbose_name='юзер бота', to=BotUser, on_delete=models.CASCADE)
    theme = models.ForeignKey(verbose_name='тема', to=Themes, on_delete=models.CASCADE, blank=True, null=False)
    sub_theme = models.ForeignKey(verbose_name='подтема', to=SubThemes, on_delete=models.CASCADE, blank=True, null=False)
    weight = models.FloatField(verbose_name='вес')

    def __str__(self):
        return f'(под)тема:{self.theme if self.theme else self.sub_theme}|юзер:{self.bot_user}|вес:{self.weight}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'вес (под)темы'
        verbose_name_plural = 'веса (под)тем'


class TlgAccounts(models.Model):
    """
    TG аккаунты для работы.
    """
    session_file = models.FileField(verbose_name='файл сессии', upload_to='sessions/', blank=False, null=True)
    acc_tlg_id = models.CharField(verbose_name='tlg_id аккаунта', max_length=50, blank=True, null=False)
    tlg_first_name = models.CharField(verbose_name='tlg_first_name', max_length=50, blank=True, null=False)
    tlg_last_name = models.CharField(verbose_name='tlg_last_name', max_length=50, blank=True, null=False)
    proxy = models.CharField(verbose_name='proxy', max_length=200, blank=True, null=False)
    is_run = models.BooleanField(verbose_name='аккаунт запущен', default=False)
    created_at = models.DateTimeField(verbose_name='дата и время добавления акка', auto_now_add=True)
    channels = models.ManyToManyField(verbose_name='каналы', to=Channels, related_name='tlg_accounts', blank=True)

    def __str__(self):
        return f'TLG Account ID=={self.acc_tlg_id}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'tlg аккаунт'
        verbose_name_plural = 'tlg аккаунты'


@receiver(pre_delete, sender=TlgAccounts)
def delete_session_file(sender, instance, **kwargs):
    """
    Функция, которая получает сигнал при удалении модели TlgAccounts и удаляет файл сессии телеграм
    """
    MY_LOGGER.info(f'Получен сигнал pre_delete от модели TlgAccounts. Выполняем soft-delete файла сессии')
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'del_sessions')):   # Если нет папки del_sessions
        os.mkdir(os.path.join(settings.MEDIA_ROOT, 'del_sessions'))     # То создаём

    if instance.session_file:
        file_path_string = os.path.join(settings.MEDIA_ROOT, instance.session_file.name)
        if os.path.exists(file_path_string):
            MY_LOGGER.debug(f'Перемещаем файл сессии {file_path_string!r} в папку "del_sessions"!')
            shutil.move(file_path_string, os.path.join(settings.MEDIA_ROOT, 'del_sessions'))


@receiver(post_save, sender=TlgAccounts)
def send_bot_command(sender, instance, created, **kwargs):
    """
    Сигнал для отправки боту команды на старт или стоп аккаунта
    """
    MY_LOGGER.info(f'Получен сигнал post_save от модели TlgAccounts.')
    if not created:
        bot_command = 'start_acc' if instance.is_run else 'stop_acc'
        MY_LOGGER.info(f'Выполним отправку боту команды: {bot_command!r}')
        command_msg = f'*&*&{bot_command} {instance.session_file.path}:{instance.pk}|'
        send_command_to_bot(command=command_msg)
