from django.test import TestCase
from mytlg.models import BotSettings
from mytlg.servises.bot_settings_service import BotSettingsService


class BotSettingsServiceTest(TestCase):

    def setUp(self):
        # Create a BotSettings object for testing
        BotSettings.objects.create(key="test_setting", value="Test Value")

    def test_get_bot_settings_by_key_existing(self):
        # Call the service method to retrieve an existing setting
        setting_value = BotSettingsService.get_bot_settings_by_key("test_setting")

        # Assert that the returned value matches the expected value
        self.assertEqual(setting_value, "Test Value")

    def test_get_bot_settings_by_key_nonexistent(self):
        # Call the service method to retrieve a nonexistent setting
        setting_value = BotSettingsService.get_bot_settings_by_key("nonexistent_setting")

        # Assert that the method returns None for a nonexistent setting
        self.assertIsNone(setting_value)
