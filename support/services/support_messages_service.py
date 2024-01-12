from support.models import SupportMessages
from django.core.exceptions import ObjectDoesNotExist

from mytlg.servises.bot_users_service import BotUsersService
from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN


class SupportMessagesService:

    @staticmethod
    def create_message(message_data: dict):
        MY_LOGGER.info(message_data)
        message = SupportMessages(
            bot_user=message_data.get('bot_user'),
            message=message_data.get('message')
        )
        message.save()
        return message

    @staticmethod
    def notify_admins(admins_list, message):
        pass

