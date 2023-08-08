import datetime
import json
from io import BytesIO

import pytz
import requests
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

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN, TIME_ZONE
from mytlg.gpt_processing import ask_the_gpt
from mytlg.models import Themes, BotUser, Channels, TlgAccounts, SubThemes, NewsPosts, AccountTasks
from mytlg.serializers import SetAccDataSerializer, ChannelsSerializer, NewsPostsSerializer, WriteNewPostSerializer, \
    WriteTaskResultSerializer
from mytlg.tasks import gpt_interests_processing, subscription_to_new_channels, scheduled_task_example


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
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid token')

        ch_pk = request.query_params.get("ch_pk")
        if not ch_pk or not ch_pk.isdigit():
            MY_LOGGER.warning(f'ch_pk невалидный или отсутствует. Значение параметра ch_pk={ch_pk}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid channel pk')

        try:
            ch_obj = Channels.objects.get(pk=int(ch_pk))  # TODO: оптимизировать запрос к БД
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не найден объект Channels по PK=={ch_pk}')
            return Response(status=status.HTTP_404_NOT_FOUND, data='channel not found')

        # Достаём все id каналов по теме
        theme_obj = ch_obj.theme if ch_obj.theme else ch_obj.sub_theme.theme
        ch_qset = Channels.objects.filter(theme=theme_obj).only("id")
        ch_ids_lst = [i_ch.pk for i_ch in ch_qset]

        # Достаём все подтемы по теме
        sub_themes_qset = SubThemes.objects.filter(theme=theme_obj).only("id")
        sub_themes_ids_lst = [i_sub_theme.pk for i_sub_theme in sub_themes_qset]
        i_ch_qset = Channels.objects.filter(sub_theme__id__in=sub_themes_ids_lst).only("id")
        [ch_ids_lst.append(i_ch.pk) for i_ch in i_ch_qset if i_ch.pk not in ch_ids_lst]

        # Складываем айдишники каналов и вытаскиваем из БД одним запросов все посты
        all_posts_lst = []
        i_ch_posts = NewsPosts.objects.filter(channel__id__in=ch_ids_lst).only("text", "embedding")
        for i_post in i_ch_posts:
            all_posts_lst.append({"text": i_post.text, "embedding": i_post.embedding})
        ser = NewsPostsSerializer(all_posts_lst, many=True)
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

                NewsPosts.objects.create(channel=ch_obj, text=ser.data.get("text"), embedding=ser.data.get("embedding"))
                return Response(data={'result': 'new post write successfull'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data}')
            return Response({'result': 'Not valid data'}, status.HTTP_400_BAD_REQUEST)


class UploadNewChannels(View):
    """
    Вьюшка для загрузки новых каналов (JSON файлы - результат парсинга tgstat).
    """

    def get(self, request):
        """
        Рендерим страничку с формой для загрузки JSON файлов с результатом парсинга.
        """
        MY_LOGGER.info(f'Получен GET запрос на вьюшку загрузки новыйх каналов из JSON файла')

        if not request.user.is_staff:
            MY_LOGGER.warning(f'Юзер, выполнивший запрос, не имеет статус staff. Редиректим для авторизации')
            return redirect(to=f'/admin/login/?next={reverse_lazy("mytlg:upload_new_channels")}')

        context = {}
        return render(request, template_name='mytlg/upload_new_channels.html', context=context)

    def post(self, request):
        """
        Обработка POST запроса, получаем файлы JSON с новыми каналами телеграм.
        """
        MY_LOGGER.info(f'Получен POST запрос на вьюшку загрузки новыйх каналов из JSON файла')

        if not request.user.is_staff:
            MY_LOGGER.warning(f'Юзер, выполнивший запрос, не имеет статус staff. Редиректим для авторизации')
            return redirect(to=f'/admin/login/?next={reverse_lazy("mytlg:upload_new_channels")}')

        for i_json_file in request.FILES.getlist("json_files"):
            i_file_dct = json.loads(i_json_file.read().decode('utf-8'))
            theme_obj, theme_created = Themes.objects.get_or_create(
                theme_name=i_file_dct.get("category").lower(),
                defaults={"theme_name": i_file_dct.get("category").lower()},
            )
            MY_LOGGER.debug(f'{"Создали" if theme_created else "Достали из БД"} тему {theme_obj}!')

            i_data = i_file_dct.get("data")
            for i_key, i_val in i_data.items():
                ch_obj, ch_created = Channels.objects.update_or_create(
                    channel_link=i_val[1],
                    defaults={
                        "channel_name": i_key,
                        "channel_link": i_val[1],
                        "subscribers_numb": int(i_val[0]),
                        "theme": theme_obj,
                    }
                )
                MY_LOGGER.debug(f'Канал {ch_obj} был {"создан" if ch_created else "обновлён"}!')

        subscription_to_new_channels.delay()
        return HttpResponse(content=f'Получил файлы, спасибо.')


class WriteTasksResults(APIView):
    """
    Вьюшки для записи результатов заданий аккаунтов.
    """
    def post(self, request):
        MY_LOGGER.info(f'Получен POST запрос на вьюшку записи результатов задачи аккаунта')

        ser = WriteTaskResultSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug(f'Данные валидны, проверяем токен')

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug(f'Токен успешно проверен')

                try:
                    task_obj = AccountTasks.objects.get(pk=int(ser.data.get("task_pk")))
                except ObjectDoesNotExist:
                    return Response(data={'result': 'account task object does not exist'},
                                    status=status.HTTP_404_NOT_FOUND)

                MY_LOGGER.debug(f'Обновляем данные в БД по задаче аккаунта c PK=={task_obj.pk}')
                task_obj.execution_result = ser.data.get("results")
                task_obj.fully_completed = ser.data.get("fully_completed")
                task_obj.completed_at = datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
                task_obj.save()

                tlg_acc = task_obj.tlg_acc

                MY_LOGGER.debug(f'Обновляем в БД каналы')
                for i_ch in ser.data.get("results"):
                    try:
                        ch_obj = Channels.objects.get(pk=int(i_ch.get("ch_pk")))
                    except ObjectDoesNotExist:
                        MY_LOGGER.warning(f'Объект канала с PK=={i_ch.get("ch_pk")} не найден в БД. Пропускаем...')
                        continue
                    if not i_ch.get("success"):
                        MY_LOGGER.debug(f'Канал {ch_obj!r} имеет success=={i_ch.get("success")}. Пропускаем...')
                        continue
                    ch_obj.channel_id = i_ch.get("ch_id")
                    ch_obj.channel_name = i_ch.get("ch_name")
                    ch_obj.description = i_ch.get("description")
                    ch_obj.subscribers_numb = i_ch.get("subscribers_numb")
                    ch_obj.is_ready = True
                    ch_obj.save()
                    tlg_acc.channels.add(ch_obj)
                    tlg_acc.subscribed_numb_of_channels += 1
                    tlg_acc.save()
                    MY_LOGGER.debug(f'Канал {ch_obj!r} обновлён и связан с аккаунтом {tlg_acc!r}.')

                return Response(data={'result': 'task result write successful'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data} | Ошибки: {ser.errors}')
            return Response(data={'result': 'Not valid data'}, status=status.HTTP_400_BAD_REQUEST)


class UpdateChannelsView(APIView):  # TODO: удалить нах, потенциальная дыра системы
    """
    Вьюшка для обновления записей каналов.
    """
    def post(self, request):
        print(request.data)
        ch_obj = Channels.objects.get(pk=int(request.data.get('pk')))
        ch_obj.channel_id = request.data.get('pk')
        ch_obj.description = request.data.get('pk')
        ch_obj.save()
        return Response(data={'result': f'{ch_obj} | {ch_obj.channel_id} | {ch_obj.description}'}, status=status.HTTP_200_OK)


def test_view(request):
    """
    Тестовая вьюшка. Тестим всякое
    """
    # themes = Themes.objects.all()
    # themes_str = '\n'.join([i_theme.theme_name for i_theme in themes])
    # rslt = ask_the_gpt(
    #     base_text=themes_str,
    #     query='Подбери подходящую тематику для следующего интереса пользователя: '
    #           '"Мне интересна лига чемпионов, составы футбольных команд, хоккей и немного шахмат"',
    #     system='Ты ответственный помощник и твоя задача - это классификация интересов пользователей по определённым '
    #            'тематикам. На вход ты будешь получать данные с информацией для ответа пользователю - '
    #            'это список тематик (каждая тематика с новой строки) и запрос пользователя, который будет содержать '
    #            'формулировку его интереса. Твоя задача определить только одну тематику из переданного списка, '
    #            'которая с большей вероятностью подходит под интерес пользователя и написать в ответ только эту '
    #            'тематику и никакого больше текста в твоём ответе не должно быть. Не придумывай ничего от себя, выбирай'
    #            ' тематику строго из того списка, который получил'
    # )
    # print(rslt)

    # file_data = b'Hello, Telegram!'  # Ваши данные для файла
    # # Создаем временный файл-буфер в памяти
    # file_buffer = BytesIO(file_data)
    #
    # files = {
    #     'document': ('myfile.txt', file_data)  # Создаем объект файла с кастомным именем
    # }
    #
    # url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    # data = {'chat_id': 1978587604, 'caption': 'test файлик'}
    # MY_LOGGER.debug(f'Выполняем запрос на отправку сообщения от лица бота, данные запроса: {data}')
    # response = requests.post(url=url, data=data, files=files)  # Выполняем запрос на отправку сообщения
    #
    # # Обрабатываем ответ
    # if response.status_code == 200:
    #     print('Файл успешно отправлен')
    # else:
    #     print('Ошибка отправки файла:', response.text)
    #
    # return HttpResponse(content=response.text)

    # scheduled_task_example.delay()
    # return HttpResponse(content='okay my friend !', status=200)

    # Получение ботом инфы о каналах
    MY_LOGGER.info(f'Получаем инфу о канале ботом')
    send_rslt = requests.post(
        url=f'https://api.telegram.org/bot{BOT_TOKEN}/getChat',
        data={
            'chat_id': '@onIy_crypto',
        }
    )
    if send_rslt.status_code == 200:
        MY_LOGGER.success(f'Успешная получена инфа о чате: {send_rslt.json()}')
    else:
        MY_LOGGER.warning(f'Не удалось отправить текст ошибки пользователю в телеграм: {send_rslt.text}')
    return HttpResponse(content='okay my friend !', status=200)