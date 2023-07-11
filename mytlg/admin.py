from django.contrib import admin

from mytlg.models import BotUser, BotSettings, Themes, Channels, SubThemes


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "tlg_id",
        "tlg_username",
        "start_bot_at",
    )
    list_display_links = (
        "pk",
        "tlg_id",
        "tlg_username",
        "start_bot_at",
    )


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "key",
        "value",
    )
    list_display_links = (
        "pk",
        "key",
        "value",
    )


@admin.register(Themes)
class ThemesAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "theme_name",
        "created_at",
    )
    list_display_links = (
        "pk",
        "theme_name",
        "created_at",
    )


@admin.register(SubThemes)
class ThemesAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "sub_theme_name",
        "created_at",
    )
    list_display_links = (
        "pk",
        "sub_theme_name",
        "created_at",
    )


@admin.register(Channels)
class ChannelsAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "channel_id",
        "channel_name",
        "channel_link",
        "created_at",
        "theme",
        "sub_theme",
    )
    list_display_links = (
        "pk",
        "channel_id",
        "channel_name",
        "channel_link",
        "created_at",
        "theme",
        "sub_theme",
    )
