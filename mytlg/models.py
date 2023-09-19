import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_delete, pre_save, m2m_changed
from django.dispatch import receiver

from cfu_mytlg_admin.settings import MY_LOGGER

from mytlg.utils import bot_command_for_start_or_stop_account


class BotUser(models.Model):
    """
    Модель для юзеров бота
    """
    tlg_id = models.CharField(verbose_name='tlg_id', max_length=30, db_index=True)
    tlg_username = models.CharField(verbose_name='username', max_length=100, blank=False, null=True)
    start_bot_at = models.DateTimeField(verbose_name='первый старт', auto_now_add=True)
    category = models.ManyToManyField(verbose_name='категории', related_name='bot_user', to='Categories', blank=True)
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
    value = models.TextField(verbose_name='значение')

    class Meta:
        ordering = ['-id']
        verbose_name = 'настройка бота'
        verbose_name_plural = 'настройки бота'


class Categories(models.Model):
    """
    Модель для таблицы с темами каналов.
    """
    category_name = models.CharField(verbose_name='имя категории', max_length=200)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)

    def __str__(self):
        return self.category_name

    class Meta:
        ordering = ['id']
        verbose_name = 'категория'
        verbose_name_plural = 'категории'


class Channels(models.Model):
    """
    Модель для таблицы с каналами к каждой тематике
    """
    channel_id = models.CharField(verbose_name='ID канала', max_length=50, blank=True, null=False)
    channel_name = models.CharField(verbose_name='название канала', max_length=150)
    channel_link = models.URLField(verbose_name='ссылка на канал', max_length=150)
    description = models.TextField(verbose_name='описание', max_length=500, blank=True, null=False)
    subscribers_numb = models.IntegerField(verbose_name='кол-во подписчиков', default=0)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)
    category = models.ForeignKey(verbose_name='категория канала', to=Categories, on_delete=models.CASCADE, blank=True, null=True)
    is_ready = models.BooleanField(verbose_name='готов', default=False)

    def __str__(self):
        return self.channel_link

    class Meta:
        ordering = ['-id']
        verbose_name = 'канал'
        verbose_name_plural = 'каналы'


class Proxys(models.Model):
    """
    Модель для таблицы хранения проксей
    """
    protocols = (
        ('socks5', 'socks5'),
        ('http', 'http'),
        ('https', 'https'),
        ('socks4', 'socks4'),
    )
    protocol = models.CharField(verbose_name='протокол', choices=protocols, max_length=6)
    host = models.CharField(verbose_name='хост', max_length=200)
    port = models.IntegerField(verbose_name='порт', default=65565)
    username = models.CharField(verbose_name='юзернейм', max_length=200, blank=True, null=True)
    password = models.CharField(verbose_name='пароль', max_length=200, blank=True, null=True)
    is_checked = models.BooleanField(verbose_name='проверена', default=False)
    last_check = models.DateTimeField(verbose_name='крайняя проверка', blank=True, null=True)

    def __str__(self):
        return (f'{self.protocol}:{self.host}:{self.port}:{self.username if self.username else ""}'
                f':{self.password if self.password else ""}')

    class Meta:
        ordering = ['-id']
        verbose_name = 'прокся'
        verbose_name_plural = 'прокси'


class TlgAccounts(models.Model):
    """
    TG аккаунты для работы.
    """
    session_file = models.FileField(verbose_name='файл сессии', upload_to='sessions/', blank=False, null=True)
    acc_tlg_id = models.CharField(verbose_name='tlg_id аккаунта', max_length=50, blank=True, null=False)
    tlg_first_name = models.CharField(verbose_name='tlg_first_name', max_length=50, blank=True, null=False)
    tlg_last_name = models.CharField(verbose_name='tlg_last_name', max_length=50, blank=True, null=False)
    # proxy = models.CharField(verbose_name='proxy', max_length=200, blank=True, null=False)
    proxy = models.ForeignKey(verbose_name='прокси', to=Proxys, on_delete=models.DO_NOTHING)
    is_run = models.BooleanField(verbose_name='аккаунт запущен', default=False)
    waiting = models.BooleanField(verbose_name='ожидание', default=False)
    banned = models.BooleanField(verbose_name='забанен', default=False)
    created_at = models.DateTimeField(verbose_name='дата и время добавления акка', auto_now_add=True)
    channels = models.ManyToManyField(verbose_name='каналы', to=Channels, related_name='tlg_accounts', blank=True)
    subscribed_numb_of_channels = models.IntegerField(verbose_name='кол-во подписок на каналы', default=0)

    def __str__(self):
        return f'TLG Account ID=={self.acc_tlg_id}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'tlg аккаунт'
        verbose_name_plural = 'tlg аккаунты'


@receiver(m2m_changed, sender=TlgAccounts.channels.through)
def update_subscribed_numb_of_channels(sender, instance, action, **kwargs):
    """
    Сигнал на изменения связей M2M. Пересчитывает кол-во каналов и записывает в нужное поле.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Вычисляем новое значение для subscribed_numb_of_channels
        instance.subscribed_numb_of_channels = instance.channels.count()
        instance.save()
        MY_LOGGER.debug(f'Пересчитали и сохранили новое кол-во каналов == {instance.channels.count()}')


@receiver(pre_delete, sender=TlgAccounts)
def delete_session_file(sender, instance, **kwargs):
    """
    Функция, которая получает сигнал при удалении модели TlgAccounts и удаляет файл сессии телеграм
    """
    if os.path.exists(instance.session_file.path):
        MY_LOGGER.debug(f'Удаляем файл сессии {instance.session_file.path!r}')
        os.remove(instance.session_file.path)
    return


@receiver(pre_save, sender=TlgAccounts)
def send_bot_command(sender, instance, **kwargs):
    """
    Сигнал для отправки боту команды на старт или стоп аккаунта
    """
    MY_LOGGER.info(f'Получен сигнал post_save от модели TlgAccounts.')

    try:
        old_instance = TlgAccounts.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        return

    if old_instance.is_run != instance.is_run:
        # TODO: разделить функционал отправки команды на старт и стоп аккаунта
        bot_command = 'start_acc' if instance.is_run else 'stop_acc'
        MY_LOGGER.info(f'Выполним отправку боту команды: {bot_command!r}')
        bot_admin = BotSettings.objects.get(key='bot_admins').value.split()[0]
        # Функция для отправки боту команды на старт или стоп аккаунта
        bot_command_for_start_or_stop_account(instance=instance, bot_command=bot_command, bot_admin=bot_admin)


class AccountsErrors(models.Model):
    """
    Модель для сохранения ошибок, с которыми сталкиваются аккаунты в процессе своей работы
    """
    error_type = models.CharField(verbose_name='тип ошибки', max_length=40)
    error_description = models.TextField(verbose_name='описание ошибки')
    created_at = models.DateTimeField(verbose_name='дата и время', auto_now_add=True)
    account = models.ForeignKey(verbose_name='аккаунт', to=TlgAccounts, on_delete=models.CASCADE)

    def short_description(self):
        return

    class Meta:
        ordering = ['-id']
        verbose_name = 'ошибка аккаунта'
        verbose_name_plural = 'ошибки аккаунтов'


class NewsPosts(models.Model):
    """
    Модель для новостных постов.
    """
    channel = models.ForeignKey(verbose_name='канал', to=Channels, on_delete=models.CASCADE)
    text = models.TextField(verbose_name='текст поста', max_length=10000)
    short_text = models.TextField(verbose_name='краткий текст', blank=True, null=True)
    post_link = models.URLField(verbose_name='ссылка на пост', blank=True, null=True)
    embedding = models.TextField(verbose_name='эмбеддинг', blank=True, null=False)
    created_at = models.DateTimeField(verbose_name='дата и время', auto_now_add=True)
    is_sent = models.BooleanField(verbose_name='отправлен пользователям', default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'новостной пост'
        verbose_name_plural = 'новостные посты'


class AccountsSubscriptionTasks(models.Model):
    """
    Модель для задач аккаунтам телеграм на подписку.
    """
    statuses = (
        ('success', 'успешно завершено'),
        ('at_work', 'в работе'),
        ('error', 'завершено с ошибкой'),
    )

    status = models.CharField(verbose_name='статус', choices=statuses, max_length=10, default='at_work')
    total_channels = models.IntegerField(verbose_name='всего каналов', default=0)
    successful_subs = models.IntegerField(verbose_name='успешная подписка', default=0)
    failed_subs = models.IntegerField(verbose_name='неудачная подписка', default=0)
    action_story = models.TextField(verbose_name='история действий')
    started_at = models.DateTimeField(verbose_name='старт', auto_now_add=True)
    ends_at = models.DateTimeField(verbose_name='окончание', blank=True, null=True)
    tlg_acc = models.ForeignKey(verbose_name='аккаунт', to=TlgAccounts, on_delete=models.CASCADE)
    initial_data = models.TextField(verbose_name='исходные данные', max_length=5000)
    channels = models.ManyToManyField(verbose_name='каналы', to=Channels,  related_name='subs_task', blank=True)

    def __str__(self):
        return f'задача на подписку для аккаунта: {self.tlg_acc!r}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'задача аккаунту на подписку'
        verbose_name_plural = 'задачи аккаунтам на подписку'


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


class ScheduledPosts(models.Model):
    """
    Посты, планируемые к отправке.
    """
    bot_user = models.ForeignKey(verbose_name='юзер бота', to=BotUser, on_delete=models.CASCADE)
    news_post = models.ForeignKey(verbose_name='пост', to=NewsPosts, on_delete=models.CASCADE)
    when_send = models.DateTimeField(verbose_name='когда отправить')
    is_sent = models.BooleanField(verbose_name='отправлено', default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'запланированный пост'
        verbose_name_plural = 'запланированные посты'
