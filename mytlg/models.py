from django.db import models


class BotUser(models.Model):
    """
    Модель для юзеров бота
    """
    tlg_id = models.CharField(verbose_name='tlg_id', max_length=30, db_index=True)
    tlg_username = models.CharField(verbose_name='username', max_length=100, blank=False, null=True)
    start_bot_at = models.DateTimeField(verbose_name='первый старт', auto_now_add=True)
    themes = models.ManyToManyField(verbose_name='тематики', related_name='bot_user', to='Themes', blank=True)
    channels = models.ManyToManyField(verbose_name='каналы', related_name='bot_user', to='Channels', blank=True)

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
        verbose_name = 'настройка Redirect Bot'
        verbose_name_plural = 'настройки Redirect Bot'


class Themes(models.Model):
    """
    Модель для таблицы с тематиками постов.
    """
    theme_name = models.CharField(verbose_name='имя тематики', max_length=200)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)

    def __str__(self):
        return self.theme_name

    class Meta:
        ordering = ['id']
        verbose_name = 'тематика'
        verbose_name_plural = 'тематики'


class Channels(models.Model):
    """
    Модель для таблицы с каналами к каждой тематике
    """
    channel_id = models.CharField(verbose_name='ID канала', max_length=50, blank=True, null=False)
    channel_name = models.CharField(verbose_name='название канала', max_length=150)
    channel_link = models.URLField(verbose_name='ссылка на канал', max_length=150)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)
    theme = models.ForeignKey(verbose_name='тематика канала', to=Themes, on_delete=models.CASCADE)

    def __str__(self):
        return self.channel_link

    class Meta:
        ordering = ['-id']
        verbose_name = 'канал'
        verbose_name_plural = 'каналы'
