from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework.views import View
from rest_framework.request import Request

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from support.serializers import SupportMessageSerializer
from support.services.support_messages_service import


class SupportMessages(View):

    def get(self):

        pass