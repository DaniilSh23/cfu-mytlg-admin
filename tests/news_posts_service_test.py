from django.test import TestCase
import datetime
from mytlg.models import NewsPosts, Channels, Categories, BotSettings
from mytlg.servises.news_posts_service import NewsPostsService, BotSettingsService
from mytlg.serializers import NewsPostsSerializer


class NewsPostsServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = Categories.objects.create(category_name="test")
        cls.channel = Channels.objects.create(
            channel_name='название канала',
            channel_link='https://t.me/+19vCK2iwUic2Y2Iy',
            description='описание',
            subscribers_numb=4,
            category=cls.category,
            is_ready=True
        )
        cls.serializer = NewsPostsSerializer()

    def test_get_posts_only_text_and_embeddings_by_channels_ids_list(self):
        # Create some NewsPosts objects associated with the channel
        NewsPosts.objects.create(
            channel=self.channel,
            text="Test Post 1",
            embedding="Test Embedding 1"
        )
        NewsPosts.objects.create(
            channel=self.channel,
            text="Test Post 2",
            embedding="Test Embedding 2"
        )

        # Call the service method
        ch_ids_lst = [self.channel.pk]

        posts = NewsPostsService.get_posts_only_text_and_embeddings_by_channels_ids_list(ch_ids_lst)

        # Assert that the posts returned match the expected values
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0].text, "Test Post 2")
        self.assertEqual(posts[0].embedding, "Test Embedding 2")
        self.assertEqual(posts[1].text, "Test Post 1")
        self.assertEqual(posts[1].embedding, "Test Embedding 1")

    def test_create_news_post(self):
        # Data for creating a news post
        ser = self.serializer
        ser._validated_data = {
            "text": "Test Post Text",
            "post_link": "http://example.com",
            "embedding": "Test Embedding",
        }
        short_post_text = "Short Test Post"

        # Call the service method to create a news post
        news_post = NewsPostsService.create_news_post(self.channel, ser, short_post_text)

        # Retrieve the created news post from the database
        created_post = NewsPosts.objects.get(pk=news_post.pk)

        # Assert that the created post matches the expected data
        self.assertEqual(created_post.channel, self.channel)
        self.assertEqual(created_post.text, "Test Post Text")
        self.assertEqual(created_post.post_link, "http://example.com")
        self.assertEqual(created_post.embedding, "Test Embedding")
        self.assertEqual(created_post.short_text, "Short Test Post")

    def test_create_news_post_no_short_post(self):
        # Data for creating a news post without a short post
        ser = self.serializer
        ser._validated_data = {
            "text": "Test Post Text",
            "post_link": "http://example.com",
            "embedding": "Test Embedding",
        }

        # Call the service method to create a news post
        news_post = NewsPostsService.create_news_post(self.channel, ser, None)

        # Retrieve the created news post from the database
        created_post = NewsPosts.objects.get(pk=news_post.pk)

        # Assert that the created post matches the expected data
        self.assertEqual(created_post.channel, self.channel)
        self.assertEqual(created_post.text, "Test Post Text")
        self.assertEqual(created_post.post_link, "http://example.com")
        self.assertEqual(created_post.embedding, "Test Embedding")
        self.assertEqual(created_post.short_text, None)  # Short text should be None

    # TODO вернуться к этому тесту после того как пофиксим баг с периодом
    def test_get_posts_by_sending_period(self):
        post_1 = NewsPosts.objects.create(
            channel=self.channel,
            text="Test Post 1",
            embedding="Test Embedding 1",
        )
        post_1.created_at = datetime.datetime.now() - datetime.timedelta(days=1)
        post_1.save()
        post_2 = NewsPosts.objects.create(
            channel=self.channel,
            text="Test Post 2",
            embedding="Test Embedding 2",
        )
        post_2.created_at = datetime.datetime.now() - datetime.timedelta(days=2)
        post_2.save()
        post_3 = NewsPosts.objects.create(
            channel=self.channel,
            text="Test Post 3",
            embedding="Test Embedding 3",
        )
        post_3.created_at = datetime.datetime.now() - datetime.timedelta(days=12)
        post_3.save()
        BotSettings.objects.create(key='period_for_what_was_interest_sec', value='604800')
        period = datetime.datetime.now() - datetime.timedelta(
            seconds=int(BotSettingsService.get_bot_settings_by_key(key='period_for_what_was_interest_sec')))
        posts = NewsPostsService.get_posts_by_sending_period()
        self.assertEqual(len(posts), 2)  # Only two post should be inside the sending period
        self.assertListEqual([post_2, post_1], list(posts))  # The post created within the period should be in the result
        self.assertNotIn(post_3, posts)
