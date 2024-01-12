from rest_framework import serializers


class SupportMessageSerializer(serializers.Serializer):
    """
    Сериалайзер для новых сообщений в поддержку.
    """
    token = serializers.CharField()
    tlg_id = serializers.CharField()
    text = serializers.CharField()
