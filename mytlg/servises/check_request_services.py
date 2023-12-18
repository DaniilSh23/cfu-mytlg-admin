from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status


class CheckRequestService:
    """
    Сервис с логикой для проверки запросов.
    """

    @staticmethod
    def check_bot_token(token: str | None, api_request: bool = True):
        if not token or token != BOT_TOKEN:
            MY_LOGGER.warning(f'Неверный токен запроса: {token} != {BOT_TOKEN}')
            response_status = status.HTTP_400_BAD_REQUEST
            response_data = 'invalid token'
            response_obj = (Response(status=response_status, data=response_data) if api_request
                            else HttpResponse(status=response_status, content=response_data))
            return response_obj

    @staticmethod
    def check_telegram_id(tlg_id: str | None, api_request: bool = True):
        """
        Проверка наличия и валидности telegram id.
        """
        if not tlg_id or not tlg_id.isdigit():
            MY_LOGGER.warning(f'tlg_id невалиден или отсутствует.')
            response_status = status.HTTP_400_BAD_REQUEST
            response_data = 'empty or invalid tlg_id'
            response_obj = (Response(status=response_status, data=response_data) if api_request
                            else HttpResponse(status=response_status, content=response_data))
            return response_obj
