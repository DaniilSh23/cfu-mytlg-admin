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
    is_run = serializers.BooleanField(required=False, allow_null=True)
    waiting = serializers.BooleanField(required=False, allow_null=True)
    banned = serializers.BooleanField(required=False, allow_null=True)


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
    text = serializers.CharField()
    embedding = serializers.CharField()


class WriteNewPostSerializer(serializers.Serializer):
    """
    Сериалайзер для записи в БД нового новостного поста.
    """
    token = serializers.CharField(max_length=50)
    ch_pk = serializers.IntegerField()
    text = serializers.CharField()
    embedding = serializers.CharField()
    post_link = serializers.URLField(required=False)


class ChildTaskResultsSerializer(serializers.Serializer):
    """
    Сериалайзер для вложенных элементов поля results в WriteTaskResultSerializer.
    Также используется в поле channels в UpdateChannelsSerializer.
    """
    ch_pk = serializers.CharField()
    success = serializers.BooleanField()
    ch_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ch_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    subscribers_numb = serializers.IntegerField(required=False, default=0)


class WriteSubsResultSerializer(serializers.Serializer):
    """
    Сериалайзер для записи в БД резульатов подписок аккаунта.
    """
    token = serializers.CharField(max_length=50)
    task_pk = serializers.IntegerField()
    actions_story = serializers.CharField()
    success_subs = serializers.IntegerField()
    fail_subs = serializers.IntegerField()
    status = serializers.CharField(max_length=10)
    end_flag = serializers.BooleanField()


class UpdateChannelsSerializer(serializers.Serializer):
    """
    Сериалайзер для обновления в БД данных о каналах
    """
    token = serializers.CharField(max_length=50)
    acc_pk = serializers.IntegerField()
    channels = ChildTaskResultsSerializer(many=True)


class AccountErrorSerializer(serializers.Serializer):
    """
    Сериалайзер для записи в БД данных об ошибке аккаунта
    """
    token = serializers.CharField(max_length=50)
    error_type = serializers.CharField(max_length=40)
    error_description = serializers.CharField()
    account = serializers.IntegerField()


class ReactionsSerializer(serializers.Serializer):
    """
    Сериалайзер для POST запроса с реакцией юзера.
    """
    tlg_id = serializers.IntegerField()
    reaction = serializers.CharField()
    post_id = serializers.IntegerField()