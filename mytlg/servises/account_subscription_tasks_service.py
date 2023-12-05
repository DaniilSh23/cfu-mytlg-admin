from mytlg.models import AccountsSubscriptionTasks
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER
import datetime

from mytlg.utils import send_message_by_bot


class AccountsSubscriptionTasksService:

    @staticmethod
    def get_account_subscription_tasks_by_pk(pk: int) -> AccountsSubscriptionTasks | None:
        try:
            return AccountsSubscriptionTasks.objects.get(pk=pk)
        except ObjectDoesNotExist:
            MY_LOGGER.info(f'AccountsSubscriptionTasks объект не найден pk == {pk}')
            return None

    @staticmethod
    def update_task_obj_data(ser, task_obj):
        task_obj.successful_subs = task_obj.successful_subs + ser.validated_data.get("success_subs")
        task_obj.failed_subs = task_obj.failed_subs + ser.validated_data.get("fail_subs")
        task_obj.action_story = f'{ser.validated_data.get("actions_story")}\n{task_obj.action_story}'
        task_obj.status = ser.validated_data.get("status")
        if ser.validated_data.get("end_flag"):
            task_obj.ends_at = datetime.datetime.now()
        task_obj.save()

    @staticmethod
    def send_subscription_notification(success: bool, channel_link: str, user_tlg_id: int):
        """
        Сервис для отправки уведомления пользователю о подписке на собственный телеграм канал.
        :param success: bool - успешная ли подписка.
        :param channel_link: str - ссылка на канал, на который была попытка подписаться.
        :param user_tlg_id: int - telegram ID пользователя, для которого выполняли подписку на канал.
        """
        MY_LOGGER.debug(f'Выполняем сервис отправки уведомления пользователю о подписке на собственный канал.')
        msg_txt = f'{"👍 Успешная" if success else "🙅‍♂️ Неудачная"} подписка на канал 🔗 {channel_link}'
        send_message_by_bot(chat_id=user_tlg_id, text=msg_txt)

    @staticmethod
    def get_subscription_tasks_in_works():
        subs_tasks_qset = (AccountsSubscriptionTasks.objects.filter(status='at_work', channels__isnull=False)
                           .only('channels', 'tlg_acc'))
        return subs_tasks_qset

    @staticmethod
    def create_subscription_task(tlg_account, channels):
        task = AccountsSubscriptionTasks.objects.create(tlg_acc=tlg_account)
        task.channels.set(channels)
        return task
