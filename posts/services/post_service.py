"""
Методы с бизнес-логикой для работы с постами.
"""
from typing import List

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import NewsPosts
from mytlg.servises.bot_settings_service import BotSettingsService
from mytlg.servises.bot_users_service import BotUsersService
from mytlg.servises.channels_service import ChannelsService
from mytlg.servises.news_posts_service import NewsPostsService
from mytlg.servises.scheduled_post_service import ScheduledPostsService
from posts.services.post_filter_service import PostFilters
from posts.services.text_process_service import TextProcessService


class PostService:
    """
    Сервис для обработки постов.
    """
    @staticmethod
    def get_posts_with_similar_category(channel_id: int):
        """
        Метод для получения из БД постов с одинаковой категорией того канала, в котором вышел новый пост.
        """
        MY_LOGGER.debug('ВЫЗВАН сервис для получения постов с общей категорией')
        ch_obj = ChannelsService.get_channel_by_channel_id(channel_id)
        if not ch_obj:
            return

        # Достаём все id каналов по теме
        theme_obj = ch_obj.category
        ch_qset = ChannelsService.get_channels_qset_only_ids(theme_obj)

        # Складываем айдишники каналов и вытаскиваем из БД одним запросов все посты
        ch_ids_lst = [i_ch.pk for i_ch in ch_qset]
        i_ch_posts = NewsPostsService.get_posts_only_text_and_embeddings_by_channels_ids_list(ch_ids_lst)
        all_posts_lst = [
            {"text": i_post.text, "embedding": i_post.embedding}
            for i_post in i_ch_posts
            if i_post.embedding
        ]

        MY_LOGGER.debug('Сервис для получения постов с общей категорией ОТРАБОТАЛ')
        return all_posts_lst

    @staticmethod
    def suitable_post_processing(post_text: str, channel_id: int, post_link: str, embedding: List[float]):
        """
        Метод для обработки подходящего поста
        """
        MY_LOGGER.debug('ВЫЗВАН сервис обработки подходящего поста.')

        # Пилим посту сокращённый варианта через ChatGPT
        text_processor = TextProcessService()
        prompt = BotSettingsService.get_bot_settings_by_key(key='prompt_for_text_reducing')
        short_post = text_processor.gpt_text_reduction(prompt=prompt, text=post_text)

        # Создаём новый пост в БД
        ch_obj = ChannelsService.get_channel_by_channel_id(channel_id)
        if not ch_obj:
            return False    # TODO: тут наверное лучше рейзить экзепшн
        new_post = NewsPosts.objects.create(
            channel=ch_obj,
            text=post_text,
            post_link=post_link,
            embedding=' '.join(list(map(lambda numb: str(numb), embedding))),
            short_text=short_post,
        )
        MY_LOGGER.success(f'Новый пост успешно создан, его PK == {new_post.pk!r}')

        # Планируем пост к отправке для конкретных юзеров
        ScheduledPostsService.scheduling_post_for_sending(post=new_post)
        MY_LOGGER.debug('Сервис обработки подходящего поста ОТРАБОТАЛ.')

    @staticmethod
    def suitable_post_processing_from_users_list(post_text: str, channel_id: int, post_link: str):
        """
        Метод для обработки подходящего поста из списка каналов, которые пользователи сами себе добавили для
        отслеживания.
        """
        MY_LOGGER.debug('ВЫЗВАН сервис обработки подходящего поста из списка кастомных каналов пользователей.')

        ch_obj = ChannelsService.get_channel_by_channel_id(channel_id)
        if not ch_obj:
            return
        # TODO: написать новый сервис для получения пользователей, у которых добавлен этот канал в список кастомных и
        #  стоит галка получать только со своих каналов - ВРОДЕ СДЕЛАЛ, НО НЕ ТЕСТИЛ.
        bot_users_qset = BotUsersService.filter_bot_users_by_channel_pk(channel_pk=ch_obj.pk)
        if len(bot_users_qset) < 1:
            MY_LOGGER.debug(f'НЕТ пользоваталей, у которых канал, где вышел пост, добавлен в список кастомных!')
            return

        # Пилим посту сокращённый варианта через ChatGPT
        embedding = TextProcessService.make_embeddings(text=post_text)
        if not embedding:
            return False
        text_processor = TextProcessService()
        prompt = BotSettingsService.get_bot_settings_by_key(key='prompt_for_text_reducing')
        short_post = text_processor.gpt_text_reduction(prompt=prompt, text=post_text)

        # Создаём новый пост в БД
        new_post = NewsPosts.objects.create(
            channel=ch_obj,
            text=post_text,
            post_link=post_link,
            embedding=' '.join(list(map(lambda numb: str(numb), embedding))),
            short_text=short_post,
            from_custom_channel=True,
        )
        MY_LOGGER.success(f'Новый пост из кастомного канала юзеров успешно создан, его PK == {new_post.pk!r}')

        # Планируем пост к отправке для конкретных юзеров
        ScheduledPostsService.planning_to_send_post_from_custom_user_channel(
            post=new_post,
            bot_users_qset=bot_users_qset
        )
        MY_LOGGER.debug('Сервис обработки подходящего поста из списка кастомных каналов пользователей ОТРАБОТАЛ.')


