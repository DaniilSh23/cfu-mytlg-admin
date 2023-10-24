from mytlg.models import NewsPosts
from mytlg.servises.bot_settings_service import BotSettingsService
import datetime
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER


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

    @staticmethod
    def get_posts_by_sending_period():
        period = int(BotSettingsService.get_bot_settings_by_key(key='period_for_what_was_interest_sec'))
        period = datetime.datetime.fromtimestamp(float(period))
        posts = NewsPosts.objects.filter(created_at__gt=period).only('embedding', 'post_link', 'short_text')
        return posts
