from django.db import models

from mytlg.models import BotUser, Categories, NewsPosts


class Interests(models.Model):
    """
    Модель для интересов пользователей
    """
    periods = (
        ('now', '⚡ сразу'),
        ('fixed_time', '🕒 фиксированное время'),
        ('every_time_period', '🔄 каждый N промежуток времени'),
    )
    interest_types_tpl = (
        ('main', 'основной'),
        ('networking', 'нетворкинг'),
        ('whats_new', 'что нового'),
    )

    interest = models.CharField(verbose_name='интерес', max_length=200)
    embedding = models.TextField(verbose_name='эмбеддинги')
    when_send = models.TimeField(verbose_name='когда присылать посты', blank=True, null=True)
    send_period = models.CharField(verbose_name='период отправки', choices=periods, blank=True, null=True)
    last_send = models.DateTimeField(verbose_name='крайняя отправка', auto_now_add=True)
    bot_user = models.ForeignKey(verbose_name='юзер бота', to=BotUser, on_delete=models.CASCADE)
    category = models.ForeignKey(verbose_name='категория', to=Categories, on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name='активен', default=True)
    interest_type = models.CharField(verbose_name='тип', choices=interest_types_tpl, max_length=15, default='main')

    class Meta:
        ordering = ['-id']
        verbose_name = 'интерес'
        verbose_name_plural = 'интересы'

    def short_interest(self):
        """
        Метод для сокращения длины формулировки интереса
        """
        if len(self.interest) > 35:
            return f"{self.interest[:35]}..."
        return self.interest


class BlackLists(models.Model):
    """
    Черные списки, создаваемые пользователями для фильтрации контента.
    """
    bot_user = models.ForeignKey(verbose_name='юзер', to=BotUser, on_delete=models.CASCADE)
    keywords = models.TextField(verbose_name='ключевые слова')

    class Meta:
        ordering = ['-id']
        verbose_name = 'черный список'
        verbose_name_plural = 'черные списки'


class Reactions(models.Model):
    """
    Модель для реакций пользователя.
    """
    bot_user = models.ForeignKey(verbose_name='юзер', to=BotUser, on_delete=models.CASCADE)
    news_post = models.ForeignKey(verbose_name='пост', to=NewsPosts, on_delete=models.CASCADE)
    reaction = models.IntegerField(verbose_name='реакция', default=0)
    created_at = models.DateTimeField(verbose_name='создана', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='изменена', blank=True, null=True, auto_now_add=False, auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'реакция'
        verbose_name_plural = 'реакции'


class CustomChannelsSettings(models.Model):
    """
    Настройки для получения новостей из кастомных каналов пользователя.
    """
    # TODO: эта модель имеет много общего с моделью Interests. В момент реализации было проще дописать ее,
    #  чем перепиливать много логики, связанной с интересами. В ходе рефакторинга стоит рассмотреть и обдумать
    #  вариант - выделения логики получения постов из кастомных каналов в отдельный интерес и взаимодействия только
    #  с моделью Interests.
    periods = (
        ('now', '⚡ сразу'),
        ('fixed_time', '🕒 фиксированное время'),
        ('every_time_period', '🔄 каждый N промежуток времени'),
    )
    bot_user = models.ForeignKey(verbose_name='юзер бота', to=BotUser, on_delete=models.CASCADE)
    when_send = models.TimeField(verbose_name='когда присылать посты', blank=True, null=True)
    send_period = models.CharField(verbose_name='период отправки', choices=periods, blank=True, null=True)
    last_send = models.DateTimeField(verbose_name='крайняя отправка', auto_now_add=True)

    def __str__(self):
        return f"Настройки кастомных каналов: {self.bot_user}"

    class Meta:
        ordering = ['id']
        verbose_name = 'настройка кастомных каналов'
        verbose_name_plural = 'настройки кастомных каналов'
