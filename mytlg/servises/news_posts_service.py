from mytlg.models import NewsPosts


class NewsPostsService:

    @staticmethod
    def get_posts_only_text_and_embeddings_by_channels_ids_list(ch_ids_lst):
        return NewsPosts.objects.filter(channel__id__in=ch_ids_lst).only("text", "embedding")

    @staticmethod
    def create_news_post(ch_obj, ser, short_post):
        news_post = NewsPosts.objects.create(
            channel=ch_obj,
            text=ser.validated_data.get("text"),
            post_link=ser.validated_data.get("post_link"),
            embedding=ser.validated_data.get("embedding"),
            short_text=short_post,
        )
        return news_post
