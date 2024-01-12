from support.models import SupportMessages
from django.core.exceptions import ObjectDoesNotExist

from mytlg.servises.bot_users_service import BotUsersService
from cfu_mytlg_admin.settings import MY_LOGGER


class SupportMessagesService:

    @staticmethod
    def create_message(message_data: dict):
        message = SupportMessages(
            bot_user=message_data.get('bot_user'),
            message=message_data.get('message')
        )
        message.save()
        return message


