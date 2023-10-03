from mytlg.models import ScheduledPosts


class ScheduledPostsService:

    @staticmethod
    def get_posts_for_show(post_hash: str) -> tuple:
        """
        Метод для получения запланированных к отправке пользователю постов
        :param post_hash:
        :return: Кортеж содержащий список словарей с запланированными постами и tlg_id пользователя
        """
        scheduled_posts = ScheduledPosts.obgects.filter(post_hash=post_hash)
        tlg_id = scheduled_posts[0].bot_user.tlg_id
        posts = [post.news_post.to_dict() for post in scheduled_posts]
        return posts, tlg_id
