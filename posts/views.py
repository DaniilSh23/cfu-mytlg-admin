from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from posts.serializers import RawChannelPostSerializer
from posts.tasks import raw_post_processing
from posts.services.post_filter_service import PostFilters

INVALID_TOKEN = 'The request token is invalid!'
BAD_REQUEST = 'The request data is invalid!'


class RawChannelPost(APIView):
    """
    Приём сырых постов.
    """
    @extend_schema(request=RawChannelPostSerializer, responses=dict, methods=['post'])
    def post(self, request: Request):
        MY_LOGGER.info(f'Получен запрос на вьюшку приёма сырых постов.')
        ser = RawChannelPostSerializer(data=request.data)

        # Проверка токена
        if BOT_TOKEN != request.data.get("token"):
            MY_LOGGER.warning(f'Неверный токен запроса. {BOT_TOKEN} != {request.data.get("token")}')
            return Response(status=403, data={"result": f"{INVALID_TOKEN} | "
                                                        f"{BOT_TOKEN} != {request.data.get('token')}"})
        if ser.is_valid():
            validated_data = ser.validated_data
            # Проверяем пост на наличие рекламы
            PostFilters.check_advertising_in_post(validated_data)
            # Вызываем таск селери для обработки поста и даём ответ на запрос
            raw_post_processing.delay(
                channel_id=validated_data.get('channel_id'),
                new_post_text=validated_data.get('text'),
                post_link=validated_data.get('post_link')
            )
            return Response(status=200, data={'result': 'OK!'})

        else:
            MY_LOGGER.warning(f'Невалидные данные запроса. | Запрос: {request.data} | Ошибки: {ser.errors}')
            return Response(status=400, data={"result": f"{BAD_REQUEST} | {ser.errors}"})
