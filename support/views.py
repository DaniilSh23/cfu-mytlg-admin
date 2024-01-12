from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages as err_msgs

from cfu_mytlg_admin.settings import MY_LOGGER
from support.services.support_messages_service import SupportMessagesService
from mytlg.servises.check_request_services import CheckRequestService
from mytlg.servises.bot_users_service import BotUsersService
from support.forms import SupportMessageForm


class SupportMessages(View):

    def get(self, request):
        MY_LOGGER.info('GET запрос на вьюшку SupportMessages')
        return render(request, template_name='support_message.html')

    def post(self, request):
        MY_LOGGER.info('Получен запрос на вьюшку приёма сообщений в саппорт.')
        form = SupportMessageForm(request.data)

        # Проверка токена
        CheckRequestService.check_bot_token(token=request.data.get("token"))
        if not form.is_valid():
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors}')
            err_msgs.error(request, 'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('support_message'))
        if form.is_valid():
            tlg_id = form.cleaned_data.get('tlg_id')
            message = form.cleaned_data.get('message')
            bot_user = BotUsersService.get_bot_user_by_tg_id(tlg_id=tlg_id)
            SupportMessagesService.create_message(message_data={'bot_user': bot_user, 'message': message})

            return HttpResponse('<p>Ваше сообщение успешно отправлено.</p>')
