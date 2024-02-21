from typing import Tuple

from django.core.exceptions import ObjectDoesNotExist

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import BotUser, NewsPosts
from user_interface.models import Reactions


class ReactionsService:
    """
    Сервис для бизнес-логики, связанной с реакциями.
    """
    @staticmethod
    def update_or_create_reactions(tlg_id: str, post_id: int, reaction: int) -> Tuple[bool, str]:
        """
        Метод для создания или обновления в БД реакции пользователя на пост.
        """
        # Получаем записи модели, связанные с Reactions
        try:
            bot_usr = BotUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'В сервисе ReactionsService.update_or_create_reactions ошибка. '
                              f'Не найден объект BotUser с tlg_id == {tlg_id}')
            return False, f'BotUser object with tlg_id == {tlg_id} does not exist'
        try:
            news_post = NewsPosts.objects.get(pk=post_id)
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'В сервисе ReactionsService.update_or_create_reactions ошибка. '
                              f'Не найден объект NewsPosts с pk == {post_id}')
            return False, f'NewsPosts object with pk == {post_id} does not exist'

        # Создаём или обновляем реакцию
        reaction, created = Reactions.objects.update_or_create(
            bot_user=bot_usr,
            news_post=news_post,
            defaults={
                "reaction": reaction,
            }
        )

        return True, f'Reaction was been {f"created with PK=={reaction.pk}" if created else f"update with value == {reaction.reaction}"}'
