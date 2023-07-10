import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib import messages as err_msgs

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from mytlg.models import Themes, BotUser, Channels
from mytlg.tasks import gpt_interests_processing
from mytlg.utils import make_form_with_channels


class WriteUsrView(APIView):
    """
    Вьюшка для обработки запросов при старте бота, записывает или обновляет данные о пользователе.
    """
    def post(self, request):
        MY_LOGGER.info(f'Получен запрос на вьюшку WriteUsrView: {request.data}')

        if not request.data.get("token") or request.data.get("token") != BOT_TOKEN:
            MY_LOGGER.warning(f'Неверный токен запроса: {request.data.get("token")} != {BOT_TOKEN}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid token')

        MY_LOGGER.debug(f'Записываем/обновляем данные о юзере в БД')
        bot_usr_obj, created = BotUser.objects.update_or_create(
            tlg_id=request.data.get("tlg_id"),
            defaults={
                "tlg_id": request.data.get("tlg_id"),
                "tlg_username": request.data.get("tlg_username"),
            }
        )
        MY_LOGGER.success(f'Данные о юзере успешно {"созданы" if created else "обновлены"} даём ответ на запрос.')
        return Response(data=f'success {"write" if created else "update"} object of bot user!',
                        status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class StartSettingsView(View):
    """
    Вьюшка для установки стартовых настроек бота
    """
    def get(self, request):
        context = {
            "themes": Themes.objects.all()
        }
        return render(request, template_name='mytlg/start_settings.html', context=context)

    @csrf_exempt
    def post(self, request):
        MY_LOGGER.info(f'Получен POST запрос для записи каналов. {request.POST}')

        MY_LOGGER.debug(f'Проверка параметров запроса')
        tlg_id = request.POST.get("tlg_id")
        selected_channels_lst = request.POST.getlist("selected_channel")
        check_selected_channels = list(map(lambda i_ch: i_ch.isdigit(), selected_channels_lst))
        if not tlg_id or not tlg_id.isdigit() or not all(check_selected_channels):
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию')
            return HttpResponse(content='Request params is not valid', status=400)

        MY_LOGGER.debug(f'Связываем в БД юзера с выбранными каналами')
        try:
            bot_usr_obj = BotUser.objects.get(tlg_id=int(tlg_id))
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Объект юзера с tlg_id=={tlg_id} не найден в БД.')
            return HttpResponse(f'User not found', status=404)

        selected_channels_lst = list(map(lambda i_ch: int(i_ch), selected_channels_lst))
        channels_qset = Channels.objects.filter(pk__in=selected_channels_lst)
        MY_LOGGER.debug(f'Получены объекты каналов для привязки к юзеру с tlg_id=={tlg_id} на основании списка '
                        f'PK={selected_channels_lst}\n{channels_qset}')
        bot_usr_obj.channels.set(channels_qset)
        return render(request, template_name='mytlg/success.html')


@csrf_exempt
def save_themes_view(request):
    """
    Вьюшка для обработки AJAX POST запроса на сохранение выбранных юзером тем,
    а также ответом новой формы в виде строки с HTML разметкой.
    """
    if request.method == 'POST':
        MY_LOGGER.info(f'Получен POST запрос для сохранения тем пользователя. {request.POST}')

        # Проверка данных запроса
        tlg_id = request.POST.get("tlg_id")
        themes_pk = request.POST.getlist("theme")
        themes_pk_check_lst = list(map(lambda pk: pk.isdigit(), themes_pk))
        themes_pk = list(map(lambda pk: int(pk), themes_pk))
        if (not tlg_id or not tlg_id.isdigit()) or not all(themes_pk_check_lst):
            MY_LOGGER.warning(f'Данные запрос не прошли валидацию!')
            return HttpResponse(content='invalid request params', status=400)

        # Записываем данные в БД
        try:
            bot_usr_obj = BotUser.objects.get(tlg_id=int(tlg_id))
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Объект юзера с tlg_id=={tlg_id} не найден в БД.')
            return HttpResponse(f'User not found', status=404)

        themes = Themes.objects.filter(pk__in=themes_pk)
        MY_LOGGER.debug(f'Получены объекты тематик для привязки к юзеру с tlg_id=={tlg_id} на основании списка '
                        f'PK={themes_pk}\n{themes}')
        bot_usr_obj.themes.set(themes)

        # Формируем и даём ответ
        new_form_html = make_form_with_channels(themes_pk, tlg_id)
        if not new_form_html:
            MY_LOGGER.warning(f'Не найдены некоторые тематики по первичным ключам из запроса. Даём ответ 404.')
            return HttpResponse(content=f'Some object Themes from primary keys list {themes_pk} does not exist',
                                status=404)
        MY_LOGGER.success(f'Даём успешный ответ на запрос')
        return HttpResponse(content=new_form_html, status=200)
    else:
        MY_LOGGER.warning(f'Получен запрос на вьюшку сохранения тем юзера с неразрешенным методом')
        return HttpResponse(content='Method not allowed', status=405)


@method_decorator(decorator=csrf_exempt, name='dispatch')
class WriteInterestsView(View):
    """
    Вьюшки обработки запросов для записи интересов пользователя
    """
    def get(self, request):
        """
        Показываем страничку с формой для заполнения 5 интересов.
        """
        MY_LOGGER.info(f'Получен GET запрос на вьюшку для записи интересов.')
        context = {
            'interest_examples': (
                'Футбол, лига чемпионов и всё в этом духе',
                'Криптовалюта, финансы и акции топовых компаний',
                'Животные, но в основном милые. Такие как котики и собачки, но не крокодилы и змеи.',
                'Технологии, искусственный интеллект и вот это вот всё',
                'Бизнес, то на чём можно зарабатывать, стартапы и прорывные идеи!'
            )
        }
        return render(request, template_name='mytlg/write_interests.html', context=context)

    def post(self, request):
        """
        Вьюшка для обработки запросов на запись интересов
        """
        MY_LOGGER.info(f'Получен POST запрос для записи интересов пользователя. {request.POST}')

        # Проверка данных запроса
        tlg_id = request.POST.get("tlg_id")
        interests = request.POST.getlist("interest")
        when_send_news = request.POST.get('when_send_news')

        check_interests = [i_interest for i_interest in interests if i_interest != '']
        if len(check_interests) < 1:
            MY_LOGGER.warning(f'Не обработан POST запрос на запись интересов. В запросе отсутствует хотя бы 1 интерес')
            err_msgs.error(request, f'Заполните хотя бы 1 интерес')
            return redirect(to=reverse_lazy('mytlg:write_interests'))

        elif not when_send_news:
            MY_LOGGER.warning(f'Не обработан POST запрос на запись интересов. '
                              f'В запросе отсутствует время, когда слать новости')
            err_msgs.error(request, f'Пожалуйста, укажите время, когда хотите получать новости!')
            return redirect(to=reverse_lazy('mytlg:write_interests'))

        elif not tlg_id or not tlg_id.isdigit():
            MY_LOGGER.warning(f'Не обработан POST запрос на запись интересов. '
                              f'В запросе отсутствует tlg_id')
            err_msgs.error(request, f'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('mytlg:write_interests'))

        MY_LOGGER.debug(f'Обрабатываем через модель GPT интересы пользователя')
        gpt_interests_processing.delay()

        MY_LOGGER.debug(f'Записываем в БД пользователю время, когда он будет получать новости')
        try:
            bot_usr_obj = BotUser.objects.get(tlg_id=int(tlg_id))
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не обработан POST запрос на запись интересов. Юзер с tlg_id=={tlg_id} не найден в БД!')
            err_msgs.error(request, f'Пользователь: Не найден Ваш профиль! Отправьте боту команду /start')
            return redirect(to=reverse_lazy('mytlg:write_interests'))
        bot_usr_obj.when_send_news = when_send_news
        bot_usr_obj.save()

        context = dict(
            header='⚙️ Настройка завершена!',
            description=f'👌 Окей. Теперь бот будет присылать Вам новости 🗞 в {when_send_news} каждый день',
            btn_text='Хорошо, спасибо!'
        )
        return render(request, template_name='mytlg/success.html', context=context)
