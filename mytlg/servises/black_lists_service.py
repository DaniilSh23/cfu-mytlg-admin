from mytlg.models import NewsPosts
from user_interface.models import BlackLists
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


class BlackListsService:

    @staticmethod
    def update_or_create(tlg_id, defaults):
        obj, created = BlackLists.objects.update_or_create(bot_user__tlg_id=tlg_id, defaults=defaults)
        return obj, created

    @staticmethod
    def get_blacklist_by_bot_user_tlg_id(tlg_id: int):
        try:
            return BlackLists.objects.get(bot_user__tlg_id=tlg_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist

    @staticmethod
    def get_blacklist_by_bot_user_only_id(bot_user_only_id):
        return BlackLists.objects.filter(bot_user=bot_user_only_id)

    @staticmethod
    def black_list_check(news_post: NewsPosts, black_list: BlackLists) -> bool:
        """
        Функция для проверки поста на предмет соответствия черному списку.
        Проверяет вхождение ключевых слов в:
            - ссылке на канал
            - названии канала
            - описании канала
            - тексте поста из канала
        Возвращает:
            False - найдено вхождение ключевых слов из черного списка, пост надо откинуть
            True - пост успешно прошёл черный список и может быть обработан далее
        """
        MY_LOGGER.debug(f'Вызвана функция для проверки поста на соответствие черному списку {black_list}')
        check_rslt = True

        # Достаём нужную инфу
        black_keywords_lst = black_list.keywords.split('\n')
        channel_link = news_post.channel.channel_link.lower()
        channel_name = news_post.channel.channel_name.lower()
        channel_description = news_post.channel.description.lower()
        post_text = news_post.text.lower()

        # Ищем вхождение ключевых слов
        for i_word in black_keywords_lst:
            for i_step in (channel_link, channel_name, channel_description, post_text):
                if i_word.lower() in i_step:
                    MY_LOGGER.warning(f'Найдено вхождение ключевого слова {i_word.lower()!r} в {i_step}. '
                                      f'Пост должен быть откинут!')
                    check_rslt = False
                    break
        if check_rslt:
            MY_LOGGER.success('Черный список пройден успешно!')
        return check_rslt
