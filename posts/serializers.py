"""
Сериализация запросов.
"""
from rest_framework import serializers


class RawChannelPostSerializer(serializers.Serializer):
    """
    Сериалайзер для новых постов из каналов.
    """
    token = serializers.CharField()
    channel_id = serializers.IntegerField()
    text = serializers.CharField()
    post_link = serializers.URLField()

