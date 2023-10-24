import datetime
import pytz
from mytlg.models import ScheduledPosts, BotUser, Interests, NewsPosts, BlackLists
from mytlg.servises.bot_users_service import BotUsersService
from mytlg.servises.black_lists_service import BlackListsService
from mytlg.servises.bot_settings_service import BotSettingsService
from mytlg.servises.interests_service import InterestsService
from mytlg.servises.text_process_service import TextProcessService
from cfu_mytlg_admin.settings import MY_LOGGER, TIME_ZONE


text_processor = TextProcessService()


class ScheduledPostsService:
    """
    Сервис для бизнес-логики, связанный с запланированными к отправке постами.
    """

    @staticmethod
    def get_posts_for_show(post_hash: str) -> tuple:
        """
        Метод для получения запланированных к отправке пользователю постов
        :param post_hash:
        :return: Кортеж содержащий список словарей с запланированными постами и tlg_id пользователя
        """
        scheduled_posts = ScheduledPosts.objects.filter(selection_hash=post_hash)
        tlg_id = scheduled_posts[0].bot_user.tlg_id
        posts = []
        for post in scheduled_posts:
            new_post = post.news_post.to_dict()
            new_post['interest'] = post.interest.interest
            posts.append(new_post)
        return posts, tlg_id

    @staticmethod
    def create_scheduled_post(i_user, interest, post, sending_datetime):
        obj = ScheduledPosts.objects.create(
            bot_user=i_user,
            news_post=post,
            when_send=sending_datetime,
            interest=interest,
        )
        MY_LOGGER.debug(f'Создана запись в таблице спланированных постов, '
                        f'спланированная дата и время отправки: {obj.when_send!r}')

    # TODO: требует рефакторинга. Эта функция вызывается при отборе постов, которые необходимо отправить конкретному юзеру
    #  по функции рекомендации нового и интересного, а также при стандартной проверке кому нужно отправить вновь вышедший
    #  в каналах пост. Я добавил здесь дополнительные параметры bot_usr, interest и логику для них, чтобы более менее
    #  привести функцию к универсальному виду. Вызывается эта функция во views.RelatedNewsView и
    #  в tasks.search_content_by_new_interest . Надо будет, короче, что-то с ней придумать, чтобы все почище было.
    @staticmethod
    def scheduling_post_for_sending(post: NewsPosts, bot_usr: BotUser = None, interest: Interests = None):
        """
        Отбор пользователей для поста и планирование поста к отправке.
        """
        MY_LOGGER.debug('Планируем пост к отправке.')
        users_qset = BotUsersService.get_users_queryset_for_scheduling_post(bot_usr)

        for i_user in users_qset:
            # Проверяем на предмет соответствия черному списку
            black_lst_qset = BlackListsService.get_blacklist_by_bot_user_only_id(i_user)
            if len(black_lst_qset) > 0:
                black_check_rslt = BlackListsService.black_list_check(news_post=post, black_list=black_lst_qset[0])
                if not black_check_rslt:
                    MY_LOGGER.warning(f'Пост {post!r} не прошёл черный список юзера {i_user!r}')
                    continue

            interests = InterestsService.filter_interest_for_scheduling_posts(i_user, interest,
                                                                              post)  # TODO: добавленная доп. логика из-за того, что функция не универсальна
            if len(interests) < 1:
                MY_LOGGER.warning(f'У юзера PK=={i_user.pk} не указаны интересы')
                continue
            interest_lst = InterestsService.create_interests_list(interests)
            # Пилим индексную базу из эмбеддингов для интересов
            index_db = text_processor.make_index_db_from_embeddings(interest_lst)
            # Находим релевантные куски подав на вход эмбеддинги
            relevant_pieces = text_processor.get_relevant_pieces_by_embeddings(index_db, post)
            # Фильтруем по векторному расстоянию подходящие куски
            filtered_rel_pieces = text_processor.filter_relevant_pieces_by_vector_distance(relevant_pieces)

            if len(filtered_rel_pieces) < 1:  # Выходим, если куски очень далеки от схожести
                MY_LOGGER.warning(f'У юзера PK=={i_user.pk} нет релевантных интересов для поста с PK=={post.pk}')
                continue

            interest, sending_datetime = InterestsService.calculate_sending_time_for_interest(filtered_rel_pieces,
                                                                                              i_user, interest,
                                                                                              interests)
            ScheduledPostsService.create_scheduled_post(i_user, interest, post, sending_datetime)

    @staticmethod
    def get_posts_that_need_to_send():
        posts = ScheduledPosts.objects.filter(
            is_sent=False,
            when_send__lte=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
        ).prefetch_related("bot_user").prefetch_related("news_post")
        return posts

    @staticmethod
    def get_scheduled_posts_by_bot_user_and_news_post_for_task(bot_user_obj, i_post):
        scheduled_posts_qset = ScheduledPosts.objects.filter(
            bot_user=bot_user_obj,
            news_post=i_post,
        ).only("when_send", "is_sent")
        return scheduled_posts_qset

    @staticmethod
    def update_when_send_for_not_sended_posts(scheduled_posts_qset):
        not_sent_posts = scheduled_posts_qset.filter(is_sent=False)
        not_sent_posts.update(when_send=datetime.datetime.now())
