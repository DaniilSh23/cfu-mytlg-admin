from django.db import models


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
        verbose_name = 'настройка Redirect Bot'
        verbose_name_plural = 'настройки Redirect Bot'


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
