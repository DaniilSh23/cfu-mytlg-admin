from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework.views import View
from rest_framework.request import Request

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from support.serializers import SupportMessageSerializer
from support.services.support_messages_service import SupportMessagesService
from mytlg.servises.check_request_services import CheckRequestService


class SupportMessages(View):

    def get(self, request):

        pass


    def post(self, request):
        MY_LOGGER.info('Получен запрос на вьюшку приёма сообщений в саппорт.')
        request_data = SupportMessageSerializer(data=request.data)

        # Проверка токена
        CheckRequestService.check_bot_token(token=request.data.get("token"))

        if request_data.is_valid():
            validated_data = request_data.validated_data
            return Response(status=200, data={'result': 'OK!'})
