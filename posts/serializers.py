"""
Сериализация запросов.
"""
from rest_framework import serializers


class RawChannelPostSerializer(serializers.Serializer):
    """
    Сериалайзер для новых постов из каналов.
    """
    token = serializers.CharField()
    ch_pk = serializers.IntegerField()
    text = serializers.CharField()
    post_link = serializers.URLField()

