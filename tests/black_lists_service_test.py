from django.test import TestCase
from mytlg.models import BlackLists, BotUser
from mytlg.servises.black_lists_service import BlackListsService
from django.core.exceptions import ObjectDoesNotExist


class BlackListsServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.bot_user = BotUser.objects.create(
            tlg_id="123456789",
            tlg_username="user_name",
            language_code="ru",
        )

    def test_update_or_create(self):
        # Call the update_or_create method with test data
        defaults = {"blocked": True}
        obj, created = BlackListsService.update_or_create(self.bot_user.tlg_id, defaults)

        # Check if the BlackLists object is created or updated correctly
        self.assertTrue(created)  # Expecting it to be created

        # Check if the BlackLists object is associated with the correct BotUser
        self.assertEqual(obj.bot_user, self.bot_user)
        self.assertTrue(obj.blocked)

        # Call the update_or_create method again to update the object
        defaults = {"blocked": False}
        obj, created = BlackListsService.update_or_create(self.bot_user.tlg_id, defaults)

        # Check if the BlackLists object is updated correctly
        self.assertFalse(created)  # Expecting it to be updated
        self.assertFalse(obj.blocked)

    def test_get_blacklist_by_bot_user_tlg_id(self):
        # Create a BlackLists object associated with the test BotUser
        BlackLists.objects.create(bot_user=self.bot_user, blocked=True)

        # Call the get_blacklist_by_bot_user_tlg_id method
        blacklist = BlackListsService.get_blacklist_by_bot_user_tlg_id(self.bot_user.tlg_id)

        # Check if the returned blacklist object is associated with the correct BotUser
        self.assertEqual(blacklist.bot_user, self.bot_user)

    def test_get_blacklist_by_bot_user_tlg_id_not_found(self):
        # Call the get_blacklist_by_bot_user_tlg_id method with an unknown tlg_id
        with self.assertRaises(ObjectDoesNotExist):
            BlackListsService.get_blacklist_by_bot_user_tlg_id(99999)
