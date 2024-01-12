from django.db import models
from mytlg.models import BotUser


class SupportMessages(models.Model):

    bot_user = models.ForeignKey(verbose_name='Пользователь бота', to=BotUser, on_delete=models.CASCADE)
    message = models.TextField(verbose_name='Сообщение', blank=True, null=False)

    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)

