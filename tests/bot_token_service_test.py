from mytlg.servises.check_request_services import CheckRequestService, BOT_TOKEN
from django.test import TestCase
from rest_framework import status


class BotTokenServiceTestCase(TestCase):

    def test_check_bot_token_valid(self):
        # Replace 'valid_token' with the actual valid token you want to test
        token = BOT_TOKEN
        response = CheckRequestService.check_bot_token(token)

        # Ensure the response status code is 200 OK
        self.assertEqual(response, None)

    def test_check_bot_token_invalid(self):
        # Replace 'invalid_token' with the actual invalid token you want to test
        token = 'invalid_token'
        response = CheckRequestService.check_bot_token(token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_bot_token_is_None(self):
        # Replace 'invalid_token' with the actual invalid token you want to test
        token = None
        response = CheckRequestService.check_bot_token(token)

        # Ensure the response status code is 400 BAD REQUEST
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
