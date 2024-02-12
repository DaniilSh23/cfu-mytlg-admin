""" ЭКШЕНЫ ДЛЯ АДМИНКИ """

from django.contrib import admin


@admin.action(description='Отметить как не готов')
def mark_channel_is_ready_param(modeladmin, request, queryset):
    """
    Отметить канал как неготовый (is_ready=False)
    """
    queryset.update(is_ready=False)


@admin.action(description='Переключить запущен/не запущен')
def switch_is_started_param(modeladmin, request, queryset):
    """
    Переключить аккаунт как запущенный (is_run=True) / не запущен (is_run=False).
    """
    for i_obj in queryset:
        i_obj.is_run = False if i_obj.is_run else True  # Переключаем запущен/не запущен.
        i_obj.save()