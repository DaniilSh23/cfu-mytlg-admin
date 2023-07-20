from rest_framework import serializers


class SetAccDataSerializer(serializers.Serializer):
    """
    Сериалайзер для установки данных модели TlgAccounts
    """
    token = serializers.CharField(max_length=50)
    acc_pk = serializers.CharField(max_length=15)
    session_file = serializers.FileField(required=False)
    acc_tlg_id = serializers.CharField(required=False)
    tlg_first_name = serializers.CharField(required=False)
    tlg_last_name = serializers.CharField(required=False)
    proxy = serializers.CharField(required=False)
    is_run = serializers.BooleanField(required=False)


class ChannelsSerializer(serializers.Serializer):
    """
    Сериалайзер для данных модели Channels
    """
    pk = serializers.IntegerField()
    channel_id = serializers.CharField()
    channel_name = serializers.URLField()
    channel_link = serializers.CharField()


class NewsPostsSerializer(serializers.Serializer):
    """
    Сериалайзер для ответа на запрос новостей по конкретной теме
    """
    posts = serializers.CharField()
    separator = serializers.CharField()


class WriteNewPostSerializer(serializers.Serializer):
    """
    Сериалайзер для записи в БД нового новостного поста.
    """
    token = serializers.CharField(max_length=50)
    ch_pk = serializers.IntegerField()
    text = serializers.CharField()