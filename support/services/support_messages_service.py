from mytlg.utils import send_message_by_bot
from support.models import SupportMessages
from django.core.exceptions import ObjectDoesNotExist

from mytlg.servises.bot_users_service import BotUsersService
from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN


class SupportMessagesService:

    @staticmethod
    def create_message(message_data: dict):
        """
        Создание сообщения для обратной связи.
        """
        MY_LOGGER.info(f"Вызван сервис по созданию сообщения ОС. | message_data: {message_data!r}")
        message = SupportMessages(
            bot_user=message_data.get('bot_user'),
            message=message_data.get('message')
        )
        message.save()
        return message

    @staticmethod
    def notify_admins(message: SupportMessages):
        """
        Уведомление админов.
        """
        MY_LOGGER.info(f"Вызван сервис для уведомления админов бота. | message: {message!r}")
        admins_tlg_ids_tpl = BotUsersService.get_bot_admins_tlg_ids()
        msg_for_send = (f"💬 Получено новое сообщение обратной связи!\n\n👤 Юзер: {message.bot_user.tlg_id}\n"
                        f"📝 Текст: {message.message}")
        [send_message_by_bot(chat_id=i_tlg_id, text=msg_for_send) for i_tlg_id in admins_tlg_ids_tpl]

