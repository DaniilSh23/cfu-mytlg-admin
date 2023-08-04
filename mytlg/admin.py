from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html

from mytlg.admin_mixins import ExportAsJSONMixin
from mytlg.models import BotUser, BotSettings, Themes, Channels, SubThemes, ThemesWeight, TlgAccounts, NewsPosts, \
    AccountTasks
from mytlg.views import UploadNewChannels


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
class ChannelsAdmin(admin.ModelAdmin, ExportAsJSONMixin):
    actions = [     # список доп. действий в админке для записей данной модели
        'export_json',   # export_csv - имя метода в миксине ExportAsCSVMixin
    ]
    list_display = (
        "pk",
        "channel_id",
        "channel_name",
        "channel_link",
        "created_at",
        "theme",
        "sub_theme",
        "is_ready",
    )
    list_display_links = (
        "pk",
        "channel_id",
        "channel_name",
        "channel_link",
        "created_at",
        "theme",
        "sub_theme",
        "is_ready",
    )


@admin.register(ThemesWeight)
class ThemesWeightAdmin(admin.ModelAdmin):
    list_display = (
        'bot_user',
        'theme',
        'sub_theme',
        'weight',
    )
    list_display_links = (
        'bot_user',
        'theme',
        'sub_theme',
        'weight',
    )


# class ChannelsInline(admin.TabularInline):
#     """
#     Отображение связанных объектов модели Channels в модели TlgAccounts
#     """
#     model = TlgAccounts.channels.through


@admin.register(TlgAccounts)
class TlgAccountsAdmin(admin.ModelAdmin):
    # inlines = [
    #     ChannelsInline,
    # ]
    list_display = (
        'pk',
        "session_file",
        "acc_tlg_id",
        "tlg_first_name",
        "tlg_last_name",
        "proxy",
        "is_run",
        "created_at",
        "subscribed_numb_of_channels",
    )
    list_display_links = (
        "pk",
        "session_file",
        "acc_tlg_id",
        "tlg_first_name",
        "tlg_last_name",
        "proxy",
        "created_at",
        "subscribed_numb_of_channels",
    )
    list_editable = (
        'is_run',
    )


@admin.register(NewsPosts)
class NewsPostsAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'is_sent',
        'created_at',
    )
    list_display_links = (
        'pk',
        'is_sent',
        'created_at',
    )

    # add_form_template = 'mytlg/upload_new_channels.html'
    # def custom_link(self, obj):
    #     url = reverse('mytlg:upload_new_channels')  # Замените 'your_custom_page' на имя вашего URL-шаблона
    #     return format_html('<a class="button" href="{}">Моя ссылка</a>', url)
    # custom_link.short_description = 'Кастомная ссылка'


@admin.register(AccountTasks)
class AccountTasksAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'task_name',
        'tlg_acc',
        'created_at',
        'completed_at',
        'fully_completed',
    )
    list_display_links = (
        'pk',
        'task_name',
        'tlg_acc',
        'created_at',
        'completed_at',
        'fully_completed',
    )
