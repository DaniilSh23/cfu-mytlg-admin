from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from rest_framework.response import Response
from rest_framework import status


class BotTokenService:

    @staticmethod
    def check_bot_token(token):
        if not token or token != BOT_TOKEN:
            MY_LOGGER.warning(f'Неверный токен запроса: {token} != {BOT_TOKEN}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid token')

