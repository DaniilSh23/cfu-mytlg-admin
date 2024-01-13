from django.contrib import admin
from support.models import SupportMessages



admin.site.site_header = 'Администрирование YOUR TELEGRAM PROJECT'


@admin.register(SupportMessages)
class SupportMessagesAdmin(admin.ModelAdmin):
    list_display = (
        "bot_user",
        "message",
        "created_at",
    )


