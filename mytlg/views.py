import datetime
import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib import messages as err_msgs

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from mytlg.common import scheduling_post_for_sending
from mytlg.forms import BlackListForm, WhatWasInterestingForm
from mytlg.gpt_processing import gpt_text_reduction
from mytlg.models import Categories, BotUser, Channels, TlgAccounts, NewsPosts, AccountsSubscriptionTasks, \
    AccountsErrors, Interests, BotSettings, BlackLists
from mytlg.serializers import SetAccDataSerializer, ChannelsSerializer, NewsPostsSerializer, WriteNewPostSerializer, \
    UpdateChannelsSerializer, AccountErrorSerializer, WriteSubsResultSerializer, ReactionsSerializer
from mytlg.servises.reactions_service import ReactionsService
from mytlg.servises.scheduled_post_service import ScheduledPostsService
from mytlg.servises.bot_users_service import BotUsersService
from mytlg.servises.categories_service import CategoriesService
from mytlg.servises.channels_service import ChannelsService
from mytlg.servises.interests_service import InterestsService
from mytlg.servises.tlg_accounts_service import TlgAccountsService
from mytlg.tasks import gpt_interests_processing, subscription_to_new_channels, start_or_stop_accounts, \
    search_content_by_new_interest


class SentReactionHandler(APIView):
    """
    Вьюшка для обработки AJAX запрос с реакцией пользователя на пост
    """

    @extend_schema(request=ReactionsSerializer, responses=dict, methods=['post'])
    def post(self, request):
        """
        Летит такой вот JSON:
        {
            'bot_usr': int,
            'post_id': int,
            'reaction': int (1 или 2)
        }
        """
        MY_LOGGER.info(f'AJAX POST запрос на вьюшку SentReactionHandler | {request.data}')
        ser = ReactionsSerializer(data=request.data)
        if ser.is_valid():

            # Вызываем сервис для выполнения бизнес логики
            service_rslt = ReactionsService.update_or_create_reactions(
                post_id=ser.validated_data.get('post_id'),
                tlg_id=ser.validated_data.get('bot_usr'),
                reaction=ser.validated_data.get('reaction'),
            )
            MY_LOGGER.debug(f'Даём ответ на AJAX POST запрос во вьюшке SentReactionHandler | '
                            f'Успешно обработан: {service_rslt[0]!r} | Описание: {service_rslt[1]!r}')
            return Response(service_rslt[1], status=200 if service_rslt[0] else 400)

        else:
            MY_LOGGER.info(f'Неудачный AJAX POST запрос на вьюшку SentReactionHandler | {request.data} | {ser.errors}')
            return Response(data={'result': f'not valid data | {ser.errors!r}'}, status=400)


class ShowScheduledPosts(View):
    """
    Вьюшка для показа запланированных постов на странице телеграм веб приложения.
    """

    def get(self, request):
        MY_LOGGER.info(f'Получен запрос на вьюшку ShowScheduledPosts {request.GET}')

        if not request.GET.get("token") or request.GET.get("token") != BOT_TOKEN:
            MY_LOGGER.warning(f'Неверный токен запроса: {request.GET.get("token")} != {BOT_TOKEN}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid token')

        post_hash = request.GET.get('post_hash')
        posts, tlg_id = ScheduledPostsService.get_posts_for_show(post_hash=post_hash)

        context = {
            "posts": posts,
            "tlg_id": tlg_id
        }
        return render(request, template_name='mytlg/show_scheduled_posts.html', context=context)


class WriteUsrView(APIView):
    """
    Вьюшка для обработки запросов при старте бота, записывает или обновляет данные о пользователе.
    """

    def post(self, request):
        MY_LOGGER.info(f'Получен запрос на вьюшку WriteUsrView: {request.data}')

        if not request.data.get("token") or request.data.get("token") != BOT_TOKEN:
            MY_LOGGER.warning(f'Неверный токен запроса: {request.data.get("token")} != {BOT_TOKEN}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid token')

        MY_LOGGER.debug('Записываем/обновляем данные о юзере в БД')

        bot_usr_obj, created = BotUsersService.update_or_create_bot_user(
            tlg_id=request.data.get("tlg_id"),
            defaults_dict={
                "tlg_id": request.data.get("tlg_id"),
                "tlg_username": request.data.get("tlg_username"),
                "language_code": request.data.get("language_code", 'ru'),
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
            "themes": CategoriesService.get_all_categories()
        }
        return render(request, template_name='mytlg/start_settings.html', context=context)

    @csrf_exempt
    def post(self, request):
        MY_LOGGER.info(f'Получен POST запрос для записи каналов. {request.POST}')

        MY_LOGGER.debug('Проверка параметров запроса')
        tlg_id = request.POST.get("tlg_id")
        selected_channels_lst = request.POST.getlist("selected_channel")
        check_selected_channels = list(map(lambda i_ch: i_ch.isdigit(), selected_channels_lst))
        if not tlg_id or not tlg_id.isdigit() or not all(check_selected_channels):
            MY_LOGGER.warning('Данные запроса не прошли валидацию')
            return HttpResponse(content='Request params is not valid', status=400)

        MY_LOGGER.debug('Связываем в БД юзера с выбранными каналами')
        bot_usr_obj = BotUsersService.get_bot_user_by_tg_id(tlg_id=int(tlg_id))

        if not bot_usr_obj:
            MY_LOGGER.warning(f'Объект юзера с tlg_id=={tlg_id} не найден в БД.')
            return HttpResponse('User not found', status=404)

        selected_channels_lst = list(map(lambda i_ch: int(i_ch), selected_channels_lst))
        channels_qset = ChannelsService.get_channels_qset_by_list_of_ids(selected_channels_lst)
        MY_LOGGER.debug(f'Получены объекты каналов для привязки к юзеру с tlg_id=={tlg_id} на основании списка '
                        f'PK={selected_channels_lst}\n{channels_qset}')
        bot_usr_obj.channels.set(channels_qset)
        return render(request, template_name='mytlg/success.html')


@method_decorator(decorator=csrf_exempt, name='dispatch')
class WriteInterestsView(View):
    """
    Вьюшки обработки запросов для записи интересов пользователя
    """
    interests_examples = (
        # 'Футбол, лига чемпионов и всё в этом духе',
        'Криптовалюта, финансы и акции топовых компаний',
        # 'Животные, но в основном милые. Такие как котики и собачки, но не крокодилы и змеи.',
        'Технологии, искусственный интеллект и вот это вот всё',
        'Бизнес, то на чём можно зарабатывать, стартапы и прорывные идеи!',
    )

    def get(self, request):
        """
        Показываем страничку с формой для заполнения 5 интересов.
        """
        MY_LOGGER.info('Получен GET запрос на вьюшку для записи интересов.')
        send_periods = Interests.periods
        context = {
            'interest_examples': self.interests_examples,
            'send_periods': send_periods,
        }
        return render(request, template_name='mytlg/write_interests.html', context=context)

    def post(self, request):
        """
        Вьюшка для обработки запросов на запись интересов
        """
        MY_LOGGER.info(f'Получен POST запрос для записи интересов пользователя. {request.POST}')

        # Проверка валидности tlg_id
        tlg_id = request.POST.get("tlg_id")
        if not tlg_id or not tlg_id.isdigit():
            MY_LOGGER.warning('Не обработан POST запрос на запись интересов. '
                              'В запросе отсутствует tlg_id')
            err_msgs.error(request, 'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('mytlg:write_interests'))

        # Проверка, что заполнен хотя бы один интерес
        interests_indxs = InterestsService.check_for_having_interests(interests_examples=self.interests_examples,
                                                                      request=request)
        if not interests_indxs:
            MY_LOGGER.warning('Не обработан POST запрос на запись интересов. В запросе отсутствует хотя бы 1 интерес')
            err_msgs.error(request, 'Заполните хотя бы 1 интерес')
            return redirect(to=reverse_lazy('mytlg:write_interests'))

        # Обработка валидного запроса
        bot_user = BotUsersService.get_bot_user_by_tg_id(tlg_id=tlg_id)
        active_interests = (InterestsService.get_active_interests(bot_user))
        InterestsService.set_is_active_false_in_active_interests(active_interests)
        new_interests_objs = InterestsService.create_list_of_new_interests_obj(interests_indxs, request)

        MY_LOGGER.debug('Обрабатываем через модели GPT интересы пользователя')
        gpt_interests_processing.delay(interests=new_interests_objs, tlg_id=tlg_id)
        context = dict(
            header='⚙️ Настройка завершена!',
            description='👌 Окей. Сейчас бот занят обработкой интересов через нейро-модели. '
                        'Нужно немного подождать, прежде чем он начнёт присылать Вам релевантные новости 🗞',
            btn_text='Хорошо, спасибо!'
        )
        return render(request, template_name='mytlg/success.html', context=context)


class SetAccFlags(APIView):
    """
    Установка флагов для аккаунта
    """

    @extend_schema(request=SetAccDataSerializer, responses=str, methods=['post'])
    def post(self, request):
        MY_LOGGER.info('Получен POST запрос на вьюшку установки флагов аккаунта')
        ser = SetAccDataSerializer(data=request.data)

        if ser.is_valid():
            MY_LOGGER.debug('Данные валидны, проверяем токен')

            if ser.validated_data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug('Токен успешно проверен')

                dct = dict()
                for i_param in ('is_run', 'waiting', 'banned'):
                    if ser.validated_data.get(i_param) is not None:
                        dct[i_param] = ser.validated_data.get(i_param)

                acc_pk = ser.validated_data.get("acc_pk")
                try:
                    MY_LOGGER.debug(f'Акк {acc_pk} | Устанавливаем следующие флаги {dct!r}')
                    TlgAccountsService.filter_and_update_tlg_account(int(acc_pk), dct)
                except ObjectDoesNotExist:
                    MY_LOGGER.warning(f'Не найден в БД объект TlgAccounts с PK={acc_pk}')
                    return Response(
                        data={'result': f'Not found object with primary key == {acc_pk}'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                return Response(data={'result': 'flags successfully changed'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. '
                                  f'Полученный токен: {ser.validated_data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data!r} | Ошибки: {ser.errors!r}')
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

        # try:
        #     # Достаём из БД каналы, с которыми связан аккаунт
        #     channels_qset = TlgAccounts.objects.get(pk=int(acc_pk)).channels.all()
        tlg_account = TlgAccountsService.get_tlg_account_by_pk(acc_pk)
        if not tlg_account:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Object does not exists')

        channels_qset = ChannelsService.get_tlg_account_channels_list(tlg_account)
        if not channels_qset:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Channels not found')
        # except ObjectDoesNotExist:
            # MY_LOGGER.warning(f'Запрошены каналы для несуществующего аккаунта (PK аккаунта == {acc_pk!r}')
            # return Response(status=status.HTTP_400_BAD_REQUEST, data='Object does not exists')

        channels_lst = ChannelsService.create_and_process_channels_lst(acc_pk, channels_qset)
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
        theme_obj = ch_obj.category
        ch_qset = Channels.objects.filter(category=theme_obj).only("id")

        # Складываем айдишники каналов и вытаскиваем из БД одним запросов все посты
        ch_ids_lst = [i_ch.pk for i_ch in ch_qset]
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
        MY_LOGGER.info('Пришёл POST запрос на вьюшку для записи нового новостного поста')
        ser = WriteNewPostSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug('Данные валидны, проверяем токен')

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug('Токен успешно проверен')

                try:
                    ch_obj = Channels.objects.get(pk=ser.data.get("ch_pk"))
                except ObjectDoesNotExist:
                    return Response(data={'result': 'channel object does not exist'})

                prompt = BotSettings.objects.get(key='prompt_for_text_reducing').value
                short_post = gpt_text_reduction(prompt=prompt, text=ser.validated_data.get("text"))

                obj = NewsPosts.objects.create(
                    channel=ch_obj,
                    text=ser.validated_data.get("text"),
                    post_link=ser.validated_data.get("post_link"),
                    embedding=ser.validated_data.get("embedding"),
                    short_text=short_post,
                )
                MY_LOGGER.success(f'Новый пост успешно создан, его PK == {obj.pk!r}')

                # Планируем пост к отправке для конкретных юзеров
                scheduling_post_for_sending(post=obj)

                return Response(data={'result': 'new post write successfull'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.POST}')
            return Response({'result': 'Not valid data'}, status.HTTP_400_BAD_REQUEST)


class UploadNewChannels(View):
    """
    Вьюшка для загрузки новых каналов (JSON файлы - результат парсинга tgstat).
    """

    def get(self, request):
        """
        Рендерим страничку с формой для загрузки JSON файлов с результатом парсинга.
        """
        MY_LOGGER.info('Получен GET запрос на вьюшку загрузки новыйх каналов из JSON файла')

        if not request.user.is_staff:
            MY_LOGGER.warning('Юзер, выполнивший запрос, не имеет статус staff. Редиректим для авторизации')
            return redirect(to=f'/admin/login/?next={reverse_lazy("mytlg:upload_new_channels")}')

        context = {}
        return render(request, template_name='mytlg/upload_new_channels.html', context=context)

    def post(self, request):
        """
        Обработка POST запроса, получаем файлы JSON с новыми каналами телеграм.
        """
        MY_LOGGER.info('Получен POST запрос на вьюшку загрузки новыйх каналов из JSON файла')

        if not request.user.is_staff:
            MY_LOGGER.warning('Юзер, выполнивший запрос, не имеет статус staff. Редиректим для авторизации')
            return redirect(to=f'/admin/login/?next={reverse_lazy("mytlg:upload_new_channels")}')

        for i_json_file in request.FILES.getlist("json_files"):
            i_file_dct = json.loads(i_json_file.read().decode('utf-8'))
            theme_obj, theme_created = Categories.objects.get_or_create(
                category_name=i_file_dct.get("category").lower(),
                defaults={"category_name": i_file_dct.get("category").lower()},
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
        return HttpResponse(content='Получил файлы, спасибо.')


class WriteSubsResults(APIView):
    """
    Вьюшки для записи результатов подписок аккаунтов.
    """

    def post(self, request):
        MY_LOGGER.info('Получен POST запрос на вьюшку записи результатов подписки аккаунта')

        ser = WriteSubsResultSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug('Данные валидны, проверяем токен')

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug('Токен успешно проверен')

                try:
                    task_obj = AccountsSubscriptionTasks.objects.get(pk=int(ser.validated_data.get("task_pk")))
                except ObjectDoesNotExist:
                    return Response(data={'result': 'account task object does not exist'},
                                    status=status.HTTP_404_NOT_FOUND)

                MY_LOGGER.debug(f'Обновляем данные в БД по задаче аккаунта c PK=={task_obj.pk}')
                task_obj.successful_subs = task_obj.successful_subs + ser.validated_data.get("success_subs")
                task_obj.failed_subs = task_obj.failed_subs + ser.validated_data.get("fail_subs")
                task_obj.action_story = f'{ser.validated_data.get("actions_story")}\n{task_obj.action_story}'
                task_obj.status = ser.validated_data.get("status")
                if ser.validated_data.get("end_flag"):
                    task_obj.ends_at = datetime.datetime.now()
                task_obj.save()

                return Response(data={'result': 'task status changed successful'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data} | Ошибки: {ser.errors}')
            return Response(data={'result': 'Not valid data'}, status=status.HTTP_400_BAD_REQUEST)


class UpdateChannelsView(APIView):
    """
    Вьюшка для обновления записей каналов.
    """

    @extend_schema(request=UpdateChannelsSerializer, responses=str, methods=['post'])
    def post(self, request):
        MY_LOGGER.info(f'Получен POST запрос на обновление данных о каналах | {request.data!r}')

        ser = UpdateChannelsSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug('Данные валидны, проверяем токен')

            if ser.data.get("token") != BOT_TOKEN:
                MY_LOGGER.warning('Токен неверный!')
                return Response(data='invalid token', status=status.HTTP_400_BAD_REQUEST)

            # Достаём объект Tlg аккаунта
            try:
                tlg_acc_obj = TlgAccounts.objects.get(pk=int(ser.data.get("acc_pk")))
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'Не найден TLG ACC с PK=={ser.data.get("acc_pk")!r}')
                return Response(data=f'Not found tlg acc with PK == {ser.data.get("acc_pk")}',
                                status=status.HTTP_404_NOT_FOUND)

            # Обрабатываем каналы
            ch_ids_lst = [int(i_ch.get("ch_pk")) for i_ch in ser.data.get('channels')]

            # TODO: кажись две строки ниже нафиг не нужны, надо пересмотреть на свежую голову
            acc_channels = tlg_acc_obj.channels.all()  # Достаём все связи с каналами для аккаунта
            [ch_ids_lst.append(i_ch.pk) for i_ch in acc_channels]

            ch_qset = Channels.objects.filter(id__in=ch_ids_lst)
            for i_ch in ch_qset:
                for j_ch in ser.data.get('channels'):
                    if int(j_ch.get("ch_pk")) == i_ch.pk:
                        new_ch_data = j_ch
                        break
                else:
                    MY_LOGGER.warning(f'В запросе не приходила инфа по каналу с PK=={i_ch.pk!r}')
                    ch_ids_lst.remove(i_ch.pk)
                    continue
                i_ch.channel_id = new_ch_data.get('ch_id')
                i_ch.channel_name = new_ch_data.get('ch_name')
                i_ch.subscribers_numb = new_ch_data.get('subscribers_numb')
                i_ch.is_ready = True

            MY_LOGGER.debug('Выполняем в транзакции 2 запроса: обновление каналов, привязка к ним акка tlg')
            with transaction.atomic():
                Channels.objects.bulk_update(ch_qset, ["channel_id", "channel_name", "subscribers_numb", "is_ready"])
                tlg_acc_obj.channels.add(*ch_ids_lst)
            MY_LOGGER.success('Запрос обработан, даём успешный ответ.')
            return Response(data={'result': 'ok'}, status=status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(f'Невалидные данные запроса. {ser.errors!r}')
            return Response(data='Invalid request data', status=status.HTTP_400_BAD_REQUEST)


class GetActiveAccounts(APIView):
    """
    Вьюшка для запроса активных аккаунтов из БД.
    """

    def get(self, request):
        """
        Обрабатываем GET запрос и отправляем боту команды на старт нужных аккаунтов.
        """
        MY_LOGGER.info('Получен GET запрос на вьюшку для получения активных аккаунтов')

        token = request.query_params.get("token")
        if not token or token != BOT_TOKEN:
            MY_LOGGER.warning(
                f'Токен неверный или отсутствует. Значение параметра token={token!r} | значение BOT_TOKEN={BOT_TOKEN!r}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid token')

        # Запускаем функцию отправки боту команд для старта аккаунтов
        start_or_stop_accounts.delay()
        return Response(data={'result': 'ok'}, status=status.HTTP_200_OK)


class AccountError(APIView):
    """
    Вьюшки для ошибок аккаунта.
    """

    @extend_schema(request=AccountErrorSerializer, responses=str, methods=['post'])
    def post(self, request):
        """
        Обрабатываем POST запрос, записываем в БД данные об ошибке аккаунта
        """
        MY_LOGGER.info('POST запрос на вьюшку ошибок аккаунта.')

        ser = AccountErrorSerializer(data=request.data)
        if ser.is_valid():
            token = ser.validated_data.get("token")
            if not token or token != BOT_TOKEN:
                MY_LOGGER.warning(f'В запросе невалидный токен: {token}')
                return Response(data='invalid token', status=status.HTTP_400_BAD_REQUEST)

            try:
                tlg_acc = TlgAccounts.objects.only("id").get(pk=ser.validated_data.get("account"))
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'Аккаунт с PK == {ser.validated_data.get("account")!r} не найден в БД.')
                return Response(data=f'account with PK == {ser.validated_data.get("account")!r} does not exist',
                                status=status.HTTP_404_NOT_FOUND)
            AccountsErrors.objects.create(
                error_type=ser.validated_data.get("error_type"),
                error_description=ser.validated_data.get("error_description"),
                account=tlg_acc,
            )
            return Response(data='success', status=status.HTTP_200_OK)
        else:
            MY_LOGGER.warning(f'Невалидные данные запроса: {request.data!r} | Ошибка: {ser.errors}')
            return Response(data=f'not valid data: {ser.errors!r}', status=status.HTTP_400_BAD_REQUEST)


class BlackListView(View):
    """
    Вьюшки для функции черного списка.
    """

    def get(self, request: HttpRequest):
        MY_LOGGER.info('Поступил GET запрос на вьюшку BlackListView')

        if request.GET.get("tlg_id") and not request.GET.get("tlg_id").isdigit:
            MY_LOGGER.warning('Параметр запроса tlg_id не является числом! Даём ответ 400')
            return HttpResponse(status=400, content='invalid query params')

        context = dict()
        if request.GET.get("tlg_id"):
            try:
                black_list = BlackLists.objects.get(bot_user__tlg_id=request.GET.get("tlg_id"))
                context["keywords"] = black_list.keywords
            except ObjectDoesNotExist:
                context["keywords_placeholder"] = ('ключевые слова (фраза) 1\nключевые слова (фраза) 2\n'
                                                   'Например: я не хочу смотреть контент про бэтмэна\n'
                                                   'И ещё не хочу смотреть контент про покемонов\n'
                                                   'Алла Пугачёва\nГруппа USB из Comedy Club')

        return render(request, 'mytlg/black_list.html', context=context)

    def post(self, request):
        MY_LOGGER.info('Поступил POST запрос на вьюшку черного списка')

        form = BlackListForm(request.POST)
        if form.is_valid():
            try:
                bot_user_obj = BotUser.objects.get(tlg_id=form.cleaned_data.get("tlg_id"))
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'В БД не найден BotUser с tlg_id=={form.cleaned_data.get("tlg_id")}')
                return HttpResponse(status=404, content='Bot User not found')

            obj, created = BlackLists.objects.update_or_create(
                bot_user__tlg_id=form.cleaned_data.get("tlg_id"),
                defaults={
                    "bot_user": bot_user_obj,
                    "keywords": form.cleaned_data.get("keywords"),
                }
            )
            MY_LOGGER.success(f'В БД {"создан" if created else "обновлён"} черный список для юзера {bot_user_obj}')
            context = dict(
                header=f'✔️ Черный список {"создан" if created else "обновлён"}',
                description='Теперь я буду фильтровать контент для Вас, если в нём будут присутствовать данные '
                            'ключевые слова',
                btn_text='Хорошо, спасибо!'
            )
            return render(request, template_name='mytlg/success.html', context=context)
        else:
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors}')
            err_msgs.error(request, 'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('mytlg:black_list'))


class WhatWasInteresting(View):
    """
    Вьюшки для опроса, что пользователю встретилось интересного.
    """

    def get(self, request):
        MY_LOGGER.info('GET запрос на вьюшку WhatWasInteresting')
        return render(request, template_name='mytlg/what_was_interesting.html')

    def post(self, request):
        MY_LOGGER.info('POST запрос на вьюшку WhatWasInteresting')
        form = WhatWasInterestingForm(request.POST)

        if form.is_valid():

            # Пробуем достать юзера бота по tlg_id
            try:
                BotUser.objects.get(tlg_id=form.cleaned_data.get("tlg_id"))
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'В БД не найден BotUser с tlg_id=={form.cleaned_data.get("tlg_id")}')
                return HttpResponse(status=404, content='Bot User not found')

            # Запускаем таск селери по обработке интереса и поиска контента
            search_content_by_new_interest.delay(
                interest=form.cleaned_data.get('interest'),
                usr_tlg_id=form.cleaned_data.get("tlg_id"),
            )

            context = dict(
                header='🔎 Окей, начинаю поиск',
                description='Я пришлю Вам подходящий контент, ожидайте.⏱',
                btn_text='Хорошо, спасибо!'
            )
            return render(request, template_name='mytlg/success.html', context=context)

        else:
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors} | Данные запроса: {request.POST}')
            for i_err in form.errors:
                err_msgs.error(request, f'Ошибка: {i_err}')
            return redirect(to=reverse_lazy('mytlg:black_list'))


def test_view(request):
    """
    Тестовая вьюшка. Тестим всякое
    """
    return HttpResponse(content='okay my friend !', status=200)
