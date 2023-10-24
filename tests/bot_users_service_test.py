from django.test import TestCase
from mytlg.models import BotUser
from mytlg.servises.bot_users_service import BotUsersService


class BotUsersServiceTest(TestCase):

    def test_get_bot_user_by_tg_id(self):
        # Create a test BotUser
        tlg_id = '12345'
        BotUser.objects.create(tlg_id=tlg_id, tlg_username="Test User")

        # Test the get_bot_user_by_tg_id method with an existing tlg_id
        bot_user = BotUsersService.get_bot_user_by_tg_id(tlg_id)

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
        tlg_id = "12345"
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
