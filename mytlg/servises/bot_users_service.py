from cfu_mytlg_admin.settings import MY_LOGGER, BOT_LINK
from mytlg.models import BotUser
from django.core.exceptions import ObjectDoesNotExist
import hashlib


class BotUsersService:

    @staticmethod
    def get_bot_user_by_tg_id(tlg_id: int) -> BotUser | None:
        try:
            return BotUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def update_or_create_bot_user(tlg_id: str, defaults_dict: dict) -> tuple:
        unique_link_part = hashlib.md5(tlg_id.encode()).hexdigest()
        defaults_dict['shared_link'] = unique_link_part
        bot_usr_obj, created = BotUser.objects.update_or_create(tlg_id=tlg_id, defaults=defaults_dict)
        return bot_usr_obj, created

    @staticmethod
    def get_all_bot_users_ids():
        return BotUser.objects.all().only('id')

    @staticmethod
    def get_bot_users_only_tlg_id():
        users = BotUser.objects.all().only('tlg_id')
        return users

    @staticmethod
    def get_users_queryset_for_scheduling_post(bot_usr):
        if not bot_usr:
            users_qset = BotUsersService.get_all_bot_users_ids()
        else:
            users_qset = (bot_usr,)  # Сделал из одного элемента кортеж, чтобы можно было итерироваться
        return users_qset

    @staticmethod
    def filter_users_queryset_without_custom_channels_flag(bot_usr):
        """
        Фильтрация пользователей, у которых не установлен флаг получения постов из своих каналов.
        """
        if not bot_usr:
            users_qset = BotUser.objects.filter(only_custom_channels=False).only("id")
        else:
            users_qset = (bot_usr,)  # Сделал из одного элемента кортеж, чтобы можно было итерироваться
        return users_qset

    @staticmethod
    def clear_bot_users_category_and_channels(tlg_id):
        bot_usr = BotUser.objects.get(tlg_id=tlg_id)
        bot_usr.category.clear()
        bot_usr.channels.clear()
        return bot_usr

    @staticmethod
    def filter_bot_users_by_ids(bot_user_ids):
        return BotUser.objects.filter(id__in=bot_user_ids)

    @staticmethod
    def get_bot_users_id_and_tlg_id_by_ids(bot_user_ids):
        bot_users = BotUser.objects.filter(id__in=bot_user_ids).only('id', 'tlg_id')
        return bot_users

    @staticmethod
    def relating_channels_with_user(user_tlg_id: int, channels_qset):
        """
        Сервис для установки связи M2M между пользователем (BotUser) и каналами (Channels).
        """
        bot_user_obj = BotUsersService.get_bot_user_by_tg_id(tlg_id=user_tlg_id)
        bot_user_obj.channels.add(*channels_qset)

    @staticmethod
    def filter_bot_users_by_channel_pk(channel_pk):
        """
        Фильтруем юзеров, у которых в числе связанных записей channel указан канал с требуемым PK
        и установлен флаг получения постов только со своих каналов.
        """
        return BotUser.objects.filter(channels__pk=channel_pk, only_custom_channels=True).only("id")

    @staticmethod
    def switch_only_custom_channels_and_get_custom_channels_lst(tlg_id: str):
        """
        Переключаем BotUser.only_custom_channels и достаем список кастомных каналов пользователя.
        Возвращаем словарь:
        {
            "only_custom_channels": True/False,   # Получать только со своих каналов
            "custom_channels_is_empty": True/False,  # Список кастомных каналов пустой
        }
        """
        try:
            bot_user = BotUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            return None

        bot_user.only_custom_channels = False if bot_user.only_custom_channels else True
        bot_user.save()
        channels = bot_user.channels.all()
        custom_channels_is_empty = False
        if not channels:
            custom_channels_is_empty = True

        return {"only_custom_channels": bot_user.only_custom_channels,
                "custom_channels_is_empty": custom_channels_is_empty}

    @staticmethod
    def get_bot_bot_admins_tlg_ids() -> tuple:
        """
        Получение кортежа tlg_id пользователей, которые являются админами бота.
        """
        MY_LOGGER.debug('Вызван сервис для получения списка tlg_id админов бота')
        try:
            bot_users = BotUser.objects.filter(is_admin=True).only("tlg_id")
        except ObjectDoesNotExist:
            return None
        return tuple(i_usr.tlg_id for i_usr in bot_users)

    @staticmethod
    def get_shared_link(tlg_id: str) -> str:
        bot_user = BotUser.objects.get(tlg_id=tlg_id)
        MY_LOGGER.info(f"Получаем уникальную ссылку для расшаривания бота lkz юзера с tlg_id = {tlg_id}")
        return f'{BOT_LINK}?start={bot_user.shared_link}'

    @staticmethod
    def increase_attracted_users_counter(source_tag: str):
        try:
            bot_user = BotUser.objects.get(shared_link=source_tag)
            bot_user.number_of_attracted_users += 1
            bot_user.save()
            MY_LOGGER.info(f'У юзера {bot_user} увеличен счетчик привлеченных пользователей, '
                           f'текущеe количество привлеченных пользователей {bot_user.number_of_attracted_users}')
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не найден юзер c shared_link - {source_tag}')

    @staticmethod
    def update_bot_user_source_tag(source_tag: str, bot_user: BotUser) -> bool:
        try:
            bot_user.source_tag = source_tag
            bot_user.save()
            return True
        except Exception as e:
            MY_LOGGER.warning(f'Ошибка при обновлении source_tag у юзера {bot_user}\n Ошибка {e}')
            return False
