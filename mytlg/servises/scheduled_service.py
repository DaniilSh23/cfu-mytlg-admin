from mytlg.models import ScheduledPosts


class ScheduledPostsService:

    @staticmethod
    def get_posts_for_show(post_hash: str) -> tuple:
        """
        Метод для получения запланированных к отправке пользователю постов
        :param post_hash:
        :return: Кортеж содержащий список словарей с запланированными постами и tlg_id пользователя
        """
        #scheduled_posts = ScheduledPosts.objects.filter(post_hash=post_hash)
        scheduled_posts = ScheduledPosts.objects.filter(bot_user__tlg_id=461767338)
        tlg_id = scheduled_posts[0].bot_user.tlg_id
        posts = []
        for post in scheduled_posts:
            new_post = post.news_post.to_dict()
            new_post['interest'] = post.interest.interest
            posts.append(new_post)
        return posts, tlg_id
