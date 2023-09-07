from django.contrib import admin

from mytlg.admin_mixins import ExportAsJSONMixin
from mytlg.models import BotUser, BotSettings, Categories, Channels, TlgAccounts, NewsPosts, \
    AccountTasks, AccountsErrors


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


@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "category_name",
        "created_at",
    )
    list_display_links = (
        "pk",
        "category_name",
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
        "category",
        "is_ready",
    )
    list_display_links = (
        "pk",
        "channel_id",
        "channel_name",
        "channel_link",
        "created_at",
        "category",
        "is_ready",
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
        'channel',
        'created_at',
    )
    list_display_links = (
        'pk',
        'is_sent',
        'channel',
        'created_at',
    )


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


@admin.register(AccountsErrors)
class AccountsErrorsAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'error_type',
        'description_short',
        'created_at',
        'account',
    )
    list_display_links = (
        'pk',
        'error_type',
        'description_short',
        'created_at',
        'account',
    )

    def description_short(self, obj: AccountsErrors) -> str:
        if len(obj.error_description) < 48:
            return obj.error_description
        return obj.error_description[:48] + "..."
