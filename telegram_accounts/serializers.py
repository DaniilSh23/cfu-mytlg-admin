from rest_framework import serializers


class OneRunningAccountSerializer(serializers.Serializer):
    """
    Сериалайзер, который описывает один запущенный аккаунт.
    """
    pk = serializers.IntegerField()
    tlg_id = serializers.IntegerField()
    proxy = serializers.CharField()
    channels_ids = serializers.ListField(child=serializers.CharField())


class RunningAccountsOutSerializer(serializers.Serializer):
    """
    Сериалайзер для данных, которые отдаем в ответ на запрос.
    """
    result = OneRunningAccountSerializer(many=True)


class BadRequestSerializer(serializers.Serializer):
    """
    Сериалайзер для отрицательного ответа на запрос
    """
    result = serializers.BooleanField(default=False)
    description = serializers.CharField()


class SessionFileOutSerializer(serializers.Serializer):
    """
    Сериалайзер для ответа на запрос файла сессии. Файл упаковывается в base64 строку.
    """
    result = serializers.BooleanField(default=False)
    file = serializers.CharField()


class SessionFileInSerializer(serializers.Serializer):
    """
    Сериалайзер для запроса файла сессии.
    """
    token = serializers.CharField()
    acc_pk = serializers.IntegerField()
