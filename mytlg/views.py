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
from mytlg.gpt_processing import ask_the_gpt
from mytlg.models import Themes, BotUser, Channels, TlgAccounts, SubThemes, NewsPosts
from mytlg.serializers import SetAccDataSerializer, ChannelsSerializer, NewsPostsSerializer, WriteNewPostSerializer
from mytlg.tasks import gpt_interests_processing


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
        gpt_interests_processing.delay(interests=check_interests, tlg_id=tlg_id)

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


class SetAccRunFlag(APIView):
    """
    Установка флага запуска аккаунта
    """
    def post(self, request):
        MY_LOGGER.info(f'Получен POST запрос на вьюшку установки флага запуска аккаунта')
        ser = SetAccDataSerializer(data=request.data)

        if ser.is_valid():
            MY_LOGGER.debug(f'Данные валидны, проверяем токен')

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug(f'Токен успешно проверен')

                try:
                    TlgAccounts.objects.filter(pk=int(ser.data.get("acc_pk"))).update(is_run=ser.data.get("is_run"))
                except ObjectDoesNotExist:
                    MY_LOGGER.warning(f'Не найден в БД объект TlgAccounts с PK={ser.data.get("acc_pk")}')
                    return Response(data={'result': f'Not found object with primary key == {ser.data.get("acc_pk")}'},
                                    status=status.HTTP_404_NOT_FOUND)

                return Response(data={'result': 'is_run flag successfully changed'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data}')
            return Response({'result': 'Not valid data'}, status.HTTP_400_BAD_REQUEST)


class GetChannelsListView(APIView):
    """
    Вьюшка для получения списка каналов для конкретного аккаунта.
    """
    def get(self, request):
        """
        В запросе необходимо передать параметр token=токен бота.
        """
        MY_LOGGER.info(f'Поступил GET запрос на вьюшку получения списка запущенных аккаунтов: {request.GET}')

        token = request.query_params.get("token")
        if not token or token != BOT_TOKEN:
            MY_LOGGER.warning(f'Токен неверный или отсутствует. Значение параметра token={token}')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        acc_pk = request.query_params.get("acc_pk")
        if not acc_pk or not acc_pk.isdigit():
            MY_LOGGER.warning(f'acc_pk невалидный или отсутствует. Значение параметра acc_pk={acc_pk}')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            channels_qset = TlgAccounts.objects.get(pk=int(acc_pk)).channels.all()
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Запрошены каналы для несуществующего аккаунта (PK аккаунта == {acc_pk!r}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Object does not exists')

        channels_lst = [
            {
                "pk": i_ch.pk,
                "channel_id": i_ch.channel_id,
                "channel_name": i_ch.channel_name,
                "channel_link": i_ch.channel_link,
            }
            for i_ch in channels_qset
        ]
        serializer = ChannelsSerializer(channels_lst, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class RelatedNewsView(APIView):
    """
    Вьюшки для новостей по определённой тематике
    """
    def get(self, request):
        """
        Получение новостей по определённой тематике. Передать PK канала.
        """
        MY_LOGGER.info(f'Получен GET запрос для получения новостей по определённой тематике: {request.GET}')

        token = request.query_params.get("token")
        if not token or token != BOT_TOKEN:
            MY_LOGGER.warning(f'Токен неверный или отсутствует. Значение параметра token={token}')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ch_pk = request.query_params.get("ch_pk")
        if not ch_pk or not ch_pk.isdigit():
            MY_LOGGER.warning(f'ch_pk невалидный или отсутствует. Значение параметра ch_pk={ch_pk}')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            ch_obj = Channels.objects.get(pk=int(ch_pk))    # TODO: дописать select_related | prefetch_related
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не найден объект Channels по PK=={ch_pk}')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Достаём все каналы по теме
        theme_obj = ch_obj.theme if ch_obj.theme else ch_obj.sub_theme.theme
        ch_qset = Channels.objects.filter(theme=theme_obj)
        channels_lst = [i_ch for i_ch in ch_qset]

        # Достаём все подтемы по теме
        sub_themes_qset = SubThemes.objects.filter(theme=theme_obj)
        for i_sub_theme in sub_themes_qset:
            i_ch_qset = Channels.objects.filter(sub_theme=i_sub_theme)
            [channels_lst.append(i_ch) for i_ch in i_ch_qset if i_ch not in channels_lst]

        # По очереди достаём из каналов посты, джойним посты по разделителю в общую строку
        all_posts_string = ''
        separator = '\n===&&&***^^^%%%===\n'
        for i_ch in channels_lst:
            i_ch_posts = NewsPosts.objects.filter(channel=i_ch)
            for i_post in i_ch_posts:
                all_posts_string = separator.join([all_posts_string, i_post.text])

        ser = NewsPostsSerializer({'posts': all_posts_string, 'separator': separator})
        return Response(data=ser.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Запись в БД нового новостного поста.
        """
        MY_LOGGER.info(f'Пришёл POST запрос на вьюшку для записи нового новостного поста: {request.POST}')
        ser = WriteNewPostSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug(f'Данные валидны, проверяем токен')

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug(f'Токен успешно проверен')

                try:
                    ch_obj = Channels.objects.get(pk=ser.data.get("ch_pk"))
                except ObjectDoesNotExist:
                    return Response(data={'result': 'channel object does not exist'})

                NewsPosts.objects.create(channel=ch_obj, text=ser.data.get("text"))
                return Response(data={'result': 'new post write successfull'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data}')
            return Response({'result': 'Not valid data'}, status.HTTP_400_BAD_REQUEST)


def test_view(request):
    """
    Тестовая вьюшка. Тестим всякое
    """
    themes = Themes.objects.all()
    themes_str = '\n'.join([i_theme.theme_name for i_theme in themes])
    rslt = ask_the_gpt(
        base_text=themes_str,
        query='Подбери подходящую тематику для следующего интереса пользователя: '
              '"Мне интересна лига чемпионов, составы футбольных команд, хоккей и немного шахмат"',
        system='Ты ответственный помощник и твоя задача - это классификация интересов пользователей по определённым '
               'тематикам. На вход ты будешь получать данные с информацией для ответа пользователю - '
               'это список тематик (каждая тематика с новой строки) и запрос пользователя, который будет содержать '
               'формулировку его интереса. Твоя задача определить только одну тематику из переданного списка, '
               'которая с большей вероятностью подходит под интерес пользователя и написать в ответ только эту '
               'тематику и никакого больше текста в твоём ответе не должно быть. Не придумывай ничего от себя, выбирай'
               ' тематику строго из того списка, который получил'
    )
    print(rslt)
    return HttpResponse(content=rslt)