from django.test import TestCase
from mytlg.models import BotUser
from mytlg.servises.bot_users_service import BotUsersService


class BotUsersServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = BotUser.objects.create(tlg_id=22222, tlg_username="Test User1")
        cls.user2 = BotUser.objects.create(tlg_id=67890, tlg_username="Test User2")

    def test_get_bot_user_by_tg_id(self):
        # Create a test BotUser
        tlg_id = '22222'

        # Test the get_bot_user_by_tg_id method with an existing tlg_id
        bot_user = BotUsersService.get_bot_user_by_tg_id(int(tlg_id))

        # Assert that the correct BotUser object is returned
        self.assertIsNotNone(bot_user)
        self.assertEqual(bot_user.tlg_id, tlg_id)

        # Test the method with a non-existing tlg_id
        non_existing_tlg_id = 54321
        bot_user = BotUsersService.get_bot_user_by_tg_id(non_existing_tlg_id)

        # Assert that None is returned for a non-existing tlg_id
        self.assertIsNone(bot_user)

    def test_update_or_create_bot_user(self):
        # Test the update_or_create_bot_user method
        tlg_id = "33333"
        defaults_dict = {"tlg_username": "Test User"}

        # Call the method to create a new BotUser
        bot_user_obj, created = BotUsersService.update_or_create_bot_user(tlg_id, defaults_dict)

        # Assert that the BotUser object is created
        self.assertTrue(created)
        self.assertEqual(bot_user_obj.tlg_id, tlg_id)
        self.assertEqual(bot_user_obj.tlg_username, "Test User")

        # Call the method again with the same tlg_id
        updated_defaults = {"tlg_username": "Updated User"}
        bot_user_obj, created = BotUsersService.update_or_create_bot_user(tlg_id, updated_defaults)

        # Assert that the BotUser object is updated and not created the second time
        self.assertFalse(created)
        self.assertEqual(bot_user_obj.tlg_id, tlg_id)
        self.assertEqual(bot_user_obj.tlg_username, "Updated User")
        bot_user_obj.delete()

    def test_get_all_bot_users_ids(self):

        # Retrieve all bot users' IDs
        result = BotUsersService.get_all_bot_users_ids()

        # Assert that the result contains the IDs of both users
        self.assertQuerysetEqual(result, [self.user2.id, self.user1.id], transform=lambda x: x.id)

    def test_get_bot_users_only_tlg_id(self):
        # Retrieve bot users' Telegram IDs
        result = BotUsersService.get_bot_users_only_tlg_id()

        # Assert that the result contains the Telegram IDs of both users
        self.assertQuerysetEqual(result, [str(self.user2.tlg_id), str(self.user1.tlg_id)], transform=lambda x: x.tlg_id)

    def test_get_users_queryset_for_scheduling_post(self):
        # Test with a bot user
        result = BotUsersService.get_users_queryset_for_scheduling_post(self.user1)
        # Assert that the result contains the bot user's ID
        self.assertQuerysetEqual(result, [self.user1.id], transform=lambda x: x.id)

        # Test without specifying a bot user
        result = BotUsersService.get_users_queryset_for_scheduling_post(None)
        # Assert that the result contains the IDs of all bot users
        self.assertQuerysetEqual(result, [self.user2.id, self.user1.id], transform=lambda x: x.id)

    def test_clear_bot_users_category_and_channels(self):
        tlg_id = self.user1.tlg_id

        # Associate a category and channels with the bot user
        self.user1.category.add(1)
        self.user1.channels.add(1)

        # Clear the bot user's category and channels
        result = BotUsersService.clear_bot_users_category_and_channels(tlg_id)

        # Assert that the bot user's category and channels are cleared
        self.assertQuerysetEqual(result.category.all(), [])
        self.assertQuerysetEqual(result.channels.all(), [])

    # def test_filter_bot_users_by_ids(self):
    #     bot_user_ids = [self.user1.id]
    #
    #     # Filter bot users by their IDs
    #     result = BotUsersService.filter_bot_users_by_ids(bot_user_ids)
    #
    #     # Assert that the result contains the bot user with the specified ID
    #     self.assertQuerysetEqual(result, [self.user1.id], transform=lambda x: x.id)
    #
    # def test_get_bot_users_id_and_tlg_id_by_ids(self):
    #     bot_user_ids = [self.user1.id, self.user2.id]
    #
    #     # Retrieve bot users' IDs and Telegram IDs by their IDs
    #     result = BotUsersService.get_bot_users_id_and_tlg_id_by_ids(bot_user_ids)
    #
    #     # Assert that the result contains the IDs and Telegram IDs of both users
    #     self.assertQuerysetEqual(result, [(self.user1.id, self.user1.tlg_id), (self.user2.id, self.user2.tlg_id)])
    #
