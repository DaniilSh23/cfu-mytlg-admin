from django.test import TestCase
from mytlg.models import Channels, TlgAccounts, Proxys, Categories
from mytlg.servises.channels_service import ChannelsService


class ChannelsServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create test TlgAccounts and Channels instances for testing
        proxy = Proxys.objects.create(
            description='описание',
            protocol_type=False,
            protocol='socks5',
            host='хост',
            port=65565,
            username='юзернейм',
            password='пароль',
            is_checked=True
        )

        cls.category = Categories.objects.create(
            category_name="Test Theme",
        )
        cls.test_channel = Channels.objects.create(
            channel_id=54321,
            channel_name="Test Channel",
            channel_link="https://test.com/channel",
            category=cls.category,
        )

        cls.test_account = TlgAccounts.objects.create(
            tlg_first_name="Test Account",
            acc_tlg_id='123',
            session_file='sessions/pyro_447388296787.session',
            proxy=proxy,
        )
        cls.test_account.channels.add(cls.test_channel)

    def test_check_selected_channels(self):
        # Test the check_selected_channels method
        selected_channels_lst = [str(self.test_channel.pk)]
        result = ChannelsService.check_selected_channels(selected_channels_lst)
        self.assertTrue(result)

    def test_get_channels_qset_by_list_of_ids(self):
        # Test the get_channels_qset_by_list_of_ids method
        selected_channels_lst = [str(self.test_channel.pk)]
        result = ChannelsService.get_channels_qset_by_list_of_ids(selected_channels_lst)
        self.assertIn(self.test_channel, result)

    def test_get_tlg_account_channels_list(self):
        # Test the get_tlg_account_channels_list method
        result = ChannelsService.get_tlg_account_channels_list(self.test_account)
        self.assertIn(self.test_channel, result)

    def test_get_channel_by_pk(self):
        # Test the get_channel_by_pk method
        result = ChannelsService.get_channel_by_channel_id(self.test_channel.pk)
        self.assertEqual(result, self.test_channel)

    # этот метод пока нигде не используется
    # def test_filter_channel_by_category(self):
    #     # Test the filter_channel_by_category method
    #     result = ChannelsService.filter_channel_by_category(category="Test Theme")
    #     self.assertIn(self.test_channel, result)

    def test_update_or_create(self):
        # Test the update_or_create method
        channel_link = "https://test.com/channel2"
        defaults = {
            "channel_name": "Test Channel 2",
            "channel_id": 12345,
            "subscribers_numb": 200,
            "category": self.category
        }
        ch_obj, ch_created = ChannelsService.update_or_create(channel_link, defaults)
        self.assertEqual(ch_obj.channel_link, channel_link)
        self.assertTrue(ch_created)
