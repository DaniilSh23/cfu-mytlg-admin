from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import path

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.admin_mixins import ExportAsJSONMixin
from mytlg.common import save_json_channels
from mytlg.forms import JSONImportForm
from mytlg.models import BotUser, BotSettings, Categories, Channels, TlgAccounts, NewsPosts, \
    AccountsErrors, AccountsSubscriptionTasks, Proxys
from mytlg.tasks import subscription_to_new_channels


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
    change_list_template = 'admin/channels_change_list.html'  # Шаблон для страницы со списком сущностей
    actions = [  # список доп. действий в админке для записей данной модели
        'export_json',  # export_csv - имя метода в миксине ExportAsCSVMixin
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

    def import_json(self, request: HttpRequest) -> HttpResponse:
        """
        Это вьюшка для кастомной формы админки, которая даёт возможность загрузить данные из файла json
        :param request:
        :return:
        """
        MY_LOGGER.info(f'Получен запрос {request.method!r} на вьюшку загрузки каналов из JSON')
        if request.method == "GET":
            # Рендерим форму
            form = JSONImportForm()
            context = {
                'form': form,
            }
            return render(request, template_name='admin/json_form.html', context=context)

        # Обрабатываем загрузку файла json
        form = JSONImportForm(request.POST, request.FILES)
        if not form.is_valid():
            # Даём ответ если форма невалидна
            context = {
                'form': form,
            }
            return render(request, template_name='admin/json_form.html', context=context, status=400)

        # Обрабатываем загруженный json файл
        save_json_channels(
            file=form.files.get("json_file").file,
            encoding=request.encoding,
        )

        # Запускаем таск celery на старт подписки аккаунтов
        subscription_to_new_channels.delay()

        # Это сообщение пользователю на странице в админке
        self.message_user(request, message='Data from JSON was imported')
        return redirect("..")  # Редиректим на одну страницу выше (к списку Product)

    def get_urls(self):
        """
        Переопределяем метод класса для того, чтобы расширить урлы для базовой страницы в админке кнопкой
        для формы загрузки данных из CSV
        :return:
        """
        urls = super().get_urls()  # Достаём дефолтные урлы класса
        new_urls = [  # Создаём свой список урлов с путём к форме
            path(
                "import-channels-json",  # Указываем путь
                self.import_json,  # Указываем вьюшку
                name="import_channels_json",
            )
        ]
        return new_urls + urls  # Обязательно новые урлы раньше дефолтных


# class ChannelsInline(admin.TabularInline):
#     """
#     Отображение связанных объектов модели Channels в модели TlgAccounts
#     """
#     model = TlgAccounts.channels.through


@admin.register(Proxys)
class ProxysAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "display_proxy_data_together",
        "is_checked",
        "last_check",
    )
    list_display_links = (
        "pk",
        "display_proxy_data_together",
        "is_checked",
        "last_check",
    )

    def display_proxy_data_together(self, obj: Proxys):
        """
        Функция для отображения данных прокси вместе, через двоеточие
        """
        return (f'{obj.protocol}:{obj.host}:{obj.port}:{obj.username if obj.username else ""}'
                f':{obj.password if obj.password else ""}')


@admin.register(TlgAccounts)
class TlgAccountsAdmin(admin.ModelAdmin):
    # inlines = [
    #     ChannelsInline,
    # ]
    list_display = (
        'pk',
        # "session_file",
        "acc_tlg_id",
        "tlg_first_name",
        "tlg_last_name",
        # "proxy",
        "is_run",
        'waiting',
        'banned',
        # "created_at",
        "subscribed_numb_of_channels",
    )
    list_display_links = (
        "pk",
        # "session_file",
        "acc_tlg_id",
        "tlg_first_name",
        "tlg_last_name",
        # "proxy",
        # "created_at",
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


@admin.register(AccountsSubscriptionTasks)
class AccountsSubscriptionTasksAdmin(admin.ModelAdmin):
    # change_list_template = 'admin/subs_tasks_change_list.html'
    list_display = (
        'pk',
        'status',
        'tlg_acc',
        'total_channels',
        'successful_subs',
        'failed_subs',
        # 'short_action_story',
        'started_at',
        'ends_at',
    )
    list_display_links = (
        'pk',
        'status',
        'tlg_acc',
        'total_channels',
        'successful_subs',
        'failed_subs',
        # 'short_action_story',
        'started_at',
        'ends_at',
    )
    list_filter = (
        'status',
    )

    def short_action_story(self, obj: AccountsSubscriptionTasks) -> str:
        """
        Функция для отображения значения поля action_story в сокращённом варианте
        """
        if len(obj.action_story) < 48:
            return obj.action_story
        return obj.action_story[:48] + "..."


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
