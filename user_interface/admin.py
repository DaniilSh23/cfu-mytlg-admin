from django.contrib import admin

from user_interface.models import Interests, BlackLists, Reactions


@admin.register(Interests)
class InterestsAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'is_active',
        'interest_short',
        'when_send',
        'send_period',
        'last_send',
        'bot_user',
        'category',
    )
    list_display_links = (
        'pk',
        'interest_short',
        'when_send',
        'send_period',
        'last_send',
        'bot_user',
        'category',
    )

    def interest_short(self, obj: Interests) -> str:
        """
        Метод для сокращения интереса пользователя при отображении в админке
        """
        if len(obj.interest) < 48:
            return obj.interest
        return obj.interest[:48] + "..."


@admin.register(BlackLists)
class BlackListsAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'bot_user',
        'keywords_short',
    )
    list_display_links = (
        'pk',
        'bot_user',
        'keywords_short',
    )

    def keywords_short(self, obj: BlackLists):
        """
        Метод для сокращенного отображения в админке поля с ключевыми словами.
        """
        if len(obj.keywords) < 48:
            return obj.keywords
        return obj.keywords[:48]


@admin.register(Reactions)
class ReactionsAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'bot_user',
        'news_post',
        'reaction',
        'created_at',
        'updated_at',
    )
    list_display_links = (
        'pk',
        'bot_user',
        'news_post',
        'reaction',
        'created_at',
        'updated_at',
    )
