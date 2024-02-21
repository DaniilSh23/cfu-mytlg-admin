from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import path

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.admin_actions import mark_channel_is_ready_param, switch_is_started_param
from mytlg.admin_mixins import ExportAsJSONMixin
from mytlg.forms import JSONImportForm
from mytlg.models import BotUser, BotSettings, Categories, Channels, TlgAccounts, NewsPosts, \
    AccountsErrors, AccountsSubscriptionTasks, Proxys, ScheduledPosts, FaqQuestion
from mytlg.tasks import subscription_to_new_channels
from mytlg.common import save_json_channels
from mytlg.servises.proxys_service import ProxysService
from mytlg.servises.proxy_providers_service import AsocksProxyService

admin.site.site_header = 'Администрирование YOUR TELEGRAM PROJECT'


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "tlg_id",
        "tlg_username",
        "start_bot_at",
        "only_custom_channels",
        "is_admin"
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


class TlgAccountsInline(admin.TabularInline):
    """
    Inline для отображения аккаунтов, которые подписаны на каналы
    """
    model = Channels.tlg_accounts.through


@admin.register(Channels)
class ChannelsAdmin(admin.ModelAdmin, ExportAsJSONMixin):
    inlines = [
        TlgAccountsInline,
    ]
    change_list_template = 'admin/channels_change_list.html'  # Шаблон для страницы со списком сущностей
    actions = [  # Список доп. действий в админке для записей данной модели
        'export_json',  # export_csv - имя метода в миксине ExportAsCSVMixin
        mark_channel_is_ready_param,  # отметить канал, как ноготовый
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
    list_filter = (
        "category",
        "is_ready",
    )
    search_fields = (
        "pk",
        "channel_id",
        "channel_name",
        "channel_link",
    )
    search_help_text = "Поиск по полям: PK, ID КАНАЛА, НАЗВАНИЕ КАНАЛА, ССЫЛКА НА КАНАЛ"

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
        files = request.FILES.getlist('json_files')
        for uploaded_file in files:
            save_json_channels(
                file=uploaded_file.file,
                encoding=request.encoding,
            )

        # Это сообщение пользователю на странице в админке
        self.message_user(request, message='Data from JSON was imported')
        return redirect("..")  # Редиректим на одну страницу выше

    def check_ch_and_start_subs(self, request: HttpRequest) -> HttpResponse:
        """
        Вьюшка для POST запроса из админки. Проверка списка каналов и запуск подписки по ним.
        """
        MY_LOGGER.info(f"Пришел запрос на вьюшку проверки каналов и запуска подписки")

        if request.method != 'POST':
            MY_LOGGER.debug(f'Запрос с неразрешенным методом {request.method!r}')
            return HttpResponse(content='Method not allowed', status=405)

        # Вызываем таск celery по старту подписок на каналы
        subscription_to_new_channels.delay()

        return redirect(to='../accountssubscriptiontasks/')

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
            ),
            path(
                "check_channels_and_start_subscription",
                self.check_ch_and_start_subs,
                name="check_channels_and_start_subscription",
            ),
        ]
        return new_urls + urls  # Обязательно новые урлы раньше дефолтных


@admin.register(Proxys)
class ProxysAdmin(admin.ModelAdmin):
    change_list_template = "admin/proxys_change_list.html"
    list_display = (
        "pk",
        "description",
        "display_proxy_data_together",
        "is_checked",
        "last_check",
    )
    list_display_links = (
        "pk",
        "description",
        "display_proxy_data_together",
        "is_checked",
        "last_check",
    )

    def get_urls(self):
        """
        Переопределяем метод класса для того, чтобы расширить урлы для базовой страницы в админке кнопкой
        для формы загрузки данных из CSV
        :return:
        """
        urls = super().get_urls()  # Достаём дефолтные урлы класса
        new_urls = [  # Создаём свой список урлов с путём к форме
            path(
                "create_asocks_proxy",  # Указываем путь
                self.create_asocks_proxy,  # Указываем вьюшку
                name="create_asocks_proxy",
            ),
        ]
        return new_urls + urls  # Обязательно новые урлы раньше дефолтных

    def display_proxy_data_together(self, obj: Proxys):
        """
        Функция для отображения данных прокси вместе, через двоеточие
        """
        return (f'{obj.protocol}:{obj.host}:{obj.port}:{obj.username if obj.username else ""}'
                f':{obj.password if obj.password else ""}')

    def create_asocks_proxy(self, request: HttpRequest) -> HttpResponse:
        """
        Функция для создания прокси на сервисе Asocks
        """
        try:
            MY_LOGGER.info('Пробуем через админку создать прокси на сервисе Asocks')
            proxy = ProxysService.create_proxy(
                proxy_data=AsocksProxyService.get_new_proxy_by_country_code(country_code='CU')
            )
            if proxy:
                MY_LOGGER.info(f'Прокси успешно создана {proxy}')
        except Exception as e:
            MY_LOGGER.warning(f'Ошибка при попытке создать через админку прокси на сервисе Asocks {e}')
        return redirect(to='../proxys/')


@admin.register(TlgAccounts)
class TlgAccountsAdmin(admin.ModelAdmin):
    actions = [
        switch_is_started_param,
    ]
    list_display = (
        'pk',
        "acc_tlg_id",
        "description",
        "is_run",
        'waiting',
        'banned',
        "subscribed_numb_of_channels",
        "proxy",
        "for_search",
    )
    list_display_links = (
        "pk",
        "acc_tlg_id",
        "description",
        "subscribed_numb_of_channels",
    )
    list_editable = (
        'is_run',
    )
    list_filter = (
        'is_run',
        'waiting',
        'banned',
        'for_search',
    )
    search_fields = (
        'pk',
        "acc_tlg_id",
        "description",
    )
    search_help_text = "Поиск по полям: PK, TLG_ID АККАУНТА, ОПИСАНИЕ"


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
    list_filter = (
        "is_sent",
    )
    search_fields = (
        "pk",
        "channel__channel_link",
        "created_at",
    )
    search_help_text = "Поиск по полям: PK, НАЗВАНИЕ КАНАЛА, ДАТА СОЗДАНИЯ ПОСТА"


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


@admin.register(ScheduledPosts)
class ScheduledPostsAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'bot_user',
        'news_post',
        'when_send',
        'is_sent',
        'selection_hash',
    )
    list_display_links = (
        'pk',
        'bot_user',
        'news_post',
        'when_send',
        'is_sent',
        'selection_hash',
    )


@admin.register(FaqQuestion)
class FaqQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'question',
        'answer',
        'created_at',
        'updated_at',
    )

    list_display_links = (
        'question',
        'answer',
        'created_at',
        'updated_at',
    )
