from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from telegram_accounts.serializers import RunningAccountsOutSerializer, BadRequestSerializer, SessionFileInSerializer, \
    SessionFileOutSerializer
from telegram_accounts.services.telegram_accounts_service import TelegramAccountService


class RunningAccountsView(APIView):
    """
    Вьюшки для запущенных аккаунтов.
    """

    # Описываем OpenAPI спецификацию для Swagger
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                required=True,
                description='токен для запроса',
                location=OpenApiParameter.QUERY,
            ),
        ],
        description='Получить аккаунты, которые должны быть запущены',
        responses={
            200: OpenApiResponse(
                description='Успешный запрос',
                response=RunningAccountsOutSerializer(),
            ),
            400: OpenApiResponse(
                description='Неверный запрос',
                response=BadRequestSerializer(),
            ),
            401: OpenApiResponse(
                description='Получен невалидный токен',
                response=BadRequestSerializer(),
            ),
            404: OpenApiResponse(
                description='Запрашиваемый контент не найден',
                response=BadRequestSerializer(),
            ),
        },
    )
    def get(self, request: Request):
        MY_LOGGER.info(f'GET запрос на вьюшку telegram_accounts.RunningAccountsView')

        # Проверка токена запроса
        if request.query_params.get('token') != BOT_TOKEN:
            MY_LOGGER.warning(f'В запросе получен невалидный токен: {request.query_params.get("token")} != {BOT_TOKEN}')
            return Response(
                data={'result': False, 'description': f'The token {request.query_params.get("token")!r} is invalid!'},
                content_type='application/json',
                status=400
            )

        # Вызов сервиса для выполнения бизнес-логики
        response_data = TelegramAccountService.get_running_accounts()
        return Response(data=response_data, content_type='application/json', status=200)


class SessionFilesView(APIView):
    """
    Обработка запросов, связанных с файлами сессий.
    """

    # Описываем OpenAPI спецификацию для Swagger
    @extend_schema(
        request=SessionFileInSerializer,
        description='Получить файл сессии для конкретного аккаунта',
        responses={
            200: OpenApiResponse(
                description='Успешный запрос',
                response=SessionFileOutSerializer,
            ),
            400: OpenApiResponse(
                description='Неверный запрос',
                response=BadRequestSerializer,
            ),
            401: OpenApiResponse(
                description='Получен невалидный токен',
                response=BadRequestSerializer,
            ),
            404: OpenApiResponse(
                description='Запрашиваемый контент не найден',
                response=BadRequestSerializer,
            ),
        },
    )
    def post(self, request):
        MY_LOGGER.info(f'POST запрос на вьюшку telegram_accounts.SessionFilesView')

        # Проверка токена запроса
        if request.data.get('token') != BOT_TOKEN:
            MY_LOGGER.warning(f'В запросе получен невалидный токен: {request.query_params.get("token")} != {BOT_TOKEN}')
            return Response(
                data={'result': False, 'description': 'invalid token'},
                content_type='application/json',
                status=400
            )

        # Вызов сервиса для выполнения бизнес-логики
        status, response_data = TelegramAccountService.get_session_file(acc_pk=request.data.get("acc_pk"))
        return Response(data=response_data, content_type='application/json', status=status)


def accounts_test_view(request):
    """
    Тестовая вьюшка.
    """