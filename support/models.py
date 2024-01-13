from django.db import models
from mytlg.models import BotUser


class SupportMessages(models.Model):
    """
    Модель для сообщений обратной связи.
    """
    bot_user = models.ForeignKey(verbose_name='пользователь бота', to=BotUser, on_delete=models.CASCADE)
    message = models.TextField(verbose_name='сообщение', blank=True, null=False)
    created_at = models.DateTimeField(verbose_name='дата и время создания', auto_now_add=True)

    class Meta:
        verbose_name = 'сообщение ОС'
        verbose_name_plural = 'сообщения ОС'
