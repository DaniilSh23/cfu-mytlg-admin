from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest
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
from django.core.cache import cache
from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN
from mytlg.forms import BlackListForm, WhatWasInterestingForm, SearchAndAddNewChannelsForm, SubscribeChannelForm
from mytlg.serializers import SetAccDataSerializer, ChannelsSerializer, NewsPostsSerializer, WriteNewPostSerializer, \
    UpdateChannelsSerializer, AccountErrorSerializer, WriteSubsResultSerializer, ReactionsSerializer
from mytlg.servises.reactions_service import ReactionsService
from mytlg.servises.scheduled_post_service import ScheduledPostsService
from mytlg.servises.bot_users_service import BotUsersService
from mytlg.servises.categories_service import CategoriesService
from mytlg.servises.channels_service import ChannelsService
from mytlg.servises.interests_service import InterestsService
from mytlg.servises.tlg_accounts_service import TlgAccountsService
from mytlg.servises.news_posts_service import NewsPostsService
from mytlg.servises.bot_settings_service import BotSettingsService
from mytlg.servises.bot_token_service import BotTokenService
from mytlg.servises.account_errors_service import TlgAccountErrorService
from mytlg.servises.black_lists_service import BlackListsService
from mytlg.servises.account_subscription_tasks_service import AccountsSubscriptionTasksService
from posts.services.text_process_service import TextProcessService
from mytlg.tasks import gpt_interests_processing, subscription_to_new_channels, start_or_stop_accounts, \
    search_content_by_new_interest

INVALID_TOKEN_TEXT = 'invalid token'
SUCCESS_TEMPLATE_PATH = 'mytlg/success.html'
CHANNEL_SEARCH_RESULTS_TEMPLATE_PATH = 'mytlg/channels_search_results.html'
NOT_VALID_DATA = 'Not valid data'
VALID_DATA_CHECK_TOKEN = 'Данные валидны, проверяем токен'
OK_THANKS = 'Хорошо, спасибо!'
TOKEN_CHECK_OK = 'Токен успешно проверен'

text_processor = TextProcessService()


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
        token = request.GET.get("token")
        bad_response = BotTokenService.check_bot_token(token)
        if bad_response:
            return bad_response
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
        token = request.data.get("token")
        BotTokenService.check_bot_token(token)

        MY_LOGGER.debug('Записываем/обновляем данные о юзере в БД')

        bot_usr_obj, created = BotUsersService.update_or_create_bot_user(
            tlg_id=request.data.get("tlg_id"),
            defaults_dict={
                "tlg_id": request.data.get("tlg_id"),
                "tlg_username": request.data.get("tlg_username"),
                "language_code": request.data.get("language_code", 'ru'),
                "source_tag": request.data.get("source_tag")
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
        return render(request, template_name=SUCCESS_TEMPLATE_PATH)


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
        send_periods = InterestsService.get_send_periods()
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
            btn_text=OK_THANKS
        )
        return render(request, template_name=SUCCESS_TEMPLATE_PATH, context=context)


class SetAccFlags(APIView):
    """
    Установка флагов для аккаунта
    """

    @extend_schema(request=SetAccDataSerializer, responses=str, methods=['post'])
    def post(self, request):
        MY_LOGGER.info('Получен POST запрос на вьюшку установки флагов аккаунта')
        ser = SetAccDataSerializer(data=request.data)

        if ser.is_valid():
            MY_LOGGER.debug(VALID_DATA_CHECK_TOKEN)

            if ser.validated_data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug(TOKEN_CHECK_OK)

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
                return Response({'result': INVALID_TOKEN_TEXT}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data!r} | Ошибки: {ser.errors!r}')
            return Response({'result': SUCCESS_TEMPLATE_PATH}, status.HTTP_400_BAD_REQUEST)


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
        BotTokenService.check_bot_token(token)

        acc_pk = request.query_params.get("acc_pk")
        if not acc_pk or not acc_pk.isdigit():
            MY_LOGGER.warning(f'acc_pk невалидный или отсутствует. Значение параметра acc_pk={acc_pk}')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        tlg_account = TlgAccountsService.get_tlg_account_by_pk(acc_pk)
        if not tlg_account:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Object does not exists')

        channels_qset = ChannelsService.get_tlg_account_channels_list(tlg_account)
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
        BotTokenService.check_bot_token(token)
        ch_pk = request.query_params.get("ch_pk")
        if not ch_pk or not ch_pk.isdigit():
            MY_LOGGER.warning(f'ch_pk невалидный или отсутствует. Значение параметра ch_pk={ch_pk}')
            return Response(status=status.HTTP_400_BAD_REQUEST, data='invalid channel pk')

        ch_obj = ChannelsService.get_channel_by_pk(ch_pk)
        if not ch_obj:
            MY_LOGGER.warning(f'Не найден объект Channels по PK=={ch_pk}')
            return Response(status=status.HTTP_404_NOT_FOUND, data='channel not found')

        # Достаём все id каналов по теме
        theme_obj = ch_obj.category
        ch_qset = ChannelsService.get_channels_qset_only_ids(theme_obj)

        # Складываем айдишники каналов и вытаскиваем из БД одним запросов все посты
        ch_ids_lst = [i_ch.pk for i_ch in ch_qset]
        all_posts_lst = []
        i_ch_posts = NewsPostsService.get_posts_only_text_and_embeddings_by_channels_ids_list(ch_ids_lst)

        for i_post in i_ch_posts:
            all_posts_lst.append({"text": i_post.text, "embedding": i_post.embedding})
        ser = NewsPostsSerializer(all_posts_lst, many=True)
        return Response(data=ser.data, status=status.HTTP_200_OK)

    @extend_schema(request=WriteNewPostSerializer, responses=str, methods=['post'])
    def post(self, request):
        """
        Запись в БД нового новостного поста.
        """
        MY_LOGGER.info('Пришёл POST запрос на вьюшку для записи нового новостного поста')
        ser = WriteNewPostSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug(VALID_DATA_CHECK_TOKEN)

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug(TOKEN_CHECK_OK)

                ch_pk = ser.data.get("ch_pk")
                ch_obj = ChannelsService.get_channel_by_pk(ch_pk)
                if not ch_obj:
                    MY_LOGGER.warning(f'Не найден объект Channels по PK=={ch_pk}')
                    return Response(data={'result': f'channel object does not exist{ch_pk}'})

                prompt = BotSettingsService.get_bot_settings_by_key(key='prompt_for_text_reducing')
                short_post = text_processor.gpt_text_reduction(prompt=prompt, text=ser.validated_data.get("text"))
                obj = NewsPostsService.create_news_post(ch_obj, ser, short_post)
                MY_LOGGER.success(f'Новый пост успешно создан, его PK == {obj.pk!r}')

                # Планируем пост к отправке для конкретных юзеров
                ScheduledPostsService.scheduling_post_for_sending(post=obj)

                return Response(data={'result': 'new post write successfull'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': INVALID_TOKEN_TEXT}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.POST}')
            return Response({'result': SUCCESS_TEMPLATE_PATH}, status.HTTP_400_BAD_REQUEST)


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

        CategoriesService.get_or_create_channels_from_json_file(request)
        subscription_to_new_channels.delay()
        return HttpResponse(content='Получил файлы, спасибо.')


class WriteSubsResults(APIView):
    """
    Вьюшки для записи результатов подписок аккаунтов.
    """

    @extend_schema(request=WriteSubsResultSerializer, responses=str, methods=['post'])
    def post(self, request):
        MY_LOGGER.info('Получен POST запрос на вьюшку записи результатов подписки аккаунта')

        ser = WriteSubsResultSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug(VALID_DATA_CHECK_TOKEN)

            if ser.data.get("token") == BOT_TOKEN:
                MY_LOGGER.debug(TOKEN_CHECK_OK)
                task_obj = AccountsSubscriptionTasksService.get_account_subscription_tasks_by_pk(
                    int(ser.validated_data.get("task_pk")))
                if not task_obj:
                    return Response(data={'result': 'account task object does not exist'},
                                    status=status.HTTP_404_NOT_FOUND)

                MY_LOGGER.debug(f'Обновляем данные в БД по задаче аккаунта c PK=={task_obj.pk}')
                AccountsSubscriptionTasksService.update_task_obj_data(ser, task_obj)

                if task_obj.tlg_acc.acc_tlg_id:
                    success_subscription = True if int(ser.validated_data.get("success_subs")) > 0 else False
                    # Отправка уведомления юзеру
                    AccountsSubscriptionTasksService.send_subscription_notification(
                        success=success_subscription,
                        channel_link=ser.validated_data.get("channel_link"),
                        user_tlg_id=task_obj.assigned_user.tlg_id,
                    )
                    if success_subscription:
                        # Получаем каналы по ссылкам на них
                        channels_qset = ChannelsService.filter_channels_by_link_only_pk(
                            channels_links=[ser.validated_data.get("channel_link")]
                        )
                        # Связываем пользователя с каналами
                        BotUsersService.relating_channels_with_user(
                            user_tlg_id=int(task_obj.assigned_user.tlg_id),
                            channels_qset=channels_qset
                        )

                return Response(data={'result': 'task status changed successful'}, status=status.HTTP_200_OK)

            else:
                MY_LOGGER.warning(f'Токен в запросе не прошёл проверку. Полученный токен: {ser.data.get("token")}')
                return Response({'result': INVALID_TOKEN_TEXT}, status=status.HTTP_400_BAD_REQUEST)

        else:
            MY_LOGGER.warning(f'Данные запроса не прошли валидацию. Запрос: {request.data} | Ошибки: {ser.errors}')
            return Response(data={'result': SUCCESS_TEMPLATE_PATH}, status=status.HTTP_400_BAD_REQUEST)


class UpdateChannelsView(APIView):
    """
    Вьюшка для обновления записей каналов.
    """

    @extend_schema(request=UpdateChannelsSerializer, responses=str, methods=['post'])
    def post(self, request):
        MY_LOGGER.info(f'Получен POST запрос на обновление данных о каналах | {request.data!r}')

        ser = UpdateChannelsSerializer(data=request.data)
        if ser.is_valid():
            MY_LOGGER.debug(VALID_DATA_CHECK_TOKEN)

            if ser.data.get("token") != BOT_TOKEN:
                MY_LOGGER.warning('Токен неверный!')
                return Response(data=INVALID_TOKEN_TEXT, status=status.HTTP_400_BAD_REQUEST)

            tlg_acc_obj = TlgAccountsService.get_tlg_account_by_pk(int(ser.data.get("acc_pk")))
            if not tlg_acc_obj:
                MY_LOGGER.warning(f'Не найден TLG ACC с PK=={ser.data.get("acc_pk")!r}')
                return Response(data=f'Not found tlg acc with PK == {ser.data.get("acc_pk")}',
                                status=status.HTTP_404_NOT_FOUND)

            # Обрабатываем каналы
            ch_ids_lst, ch_qset = ChannelsService.process_tlg_channels(ser)
            ChannelsService.bulk_update_channels(ch_ids_lst, ch_qset, tlg_acc_obj)
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
        BotTokenService.check_bot_token(token)
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

        if not ser.is_valid():
            MY_LOGGER.warning(f'Невалидные данные запроса: {request.data!r} | Ошибка: {ser.errors}')
            return Response(data=f'not valid data: {ser.errors!r}', status=status.HTTP_400_BAD_REQUEST)

        token = ser.validated_data.get("token")
        BotTokenService.check_bot_token(token)
        pk = ser.validated_data.get("account")
        tlg_acc = TlgAccountsService.get_tlg_account_only_id_by_pk(pk)

        if not tlg_acc:
            return Response(data=f'account with PK == {pk!r} does not exist',
                            status=status.HTTP_404_NOT_FOUND)

        TlgAccountErrorService.create_tlg_account_error(ser, tlg_acc)
        return Response(data='success', status=status.HTTP_200_OK)


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
                black_list = BlackListsService.get_blacklist_by_bot_user_tlg_id(tlg_id=request.GET.get("tlg_id"))
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
        if not form.is_valid():
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors}')
            err_msgs.error(request, 'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('mytlg:black_list'))
        tlg_id = form.cleaned_data.get("tlg_id")
        bot_user_obj = BotUsersService.get_bot_user_by_tg_id(tlg_id)
        if not bot_user_obj:
            MY_LOGGER.warning(f'В БД не найден BotUser с tlg_id=={tlg_id}')
            return HttpResponse(status=404, content='Bot User not found')

        obj, created = BlackListsService.update_or_create(
            tlg_id=form.cleaned_data.get("tlg_id"),
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
            btn_text=OK_THANKS
        )
        return render(request, template_name=SUCCESS_TEMPLATE_PATH, context=context)


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

        if not form.is_valid():
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors} | Данные запроса: {request.POST}')
            for i_err in form.errors:
                err_msgs.error(request, f'Ошибка: {i_err}')
            return redirect(to=reverse_lazy('mytlg:black_list'))
        # Пробуем достать юзера бота по tlg_id
        tlg_id = form.cleaned_data.get("tlg_id")
        bot_user_obj = BotUsersService.get_bot_user_by_tg_id(tlg_id)
        if not bot_user_obj:
            MY_LOGGER.warning(f'В БД не найден BotUser с tlg_id=={tlg_id}')
            return HttpResponse(status=404, content='Bot User not found')

        # Запускаем таск селери по обработке интереса и поиска контента
        search_content_by_new_interest.delay(
            interest=form.cleaned_data.get('interest'),
            usr_tlg_id=form.cleaned_data.get("tlg_id"),
        )

        context = dict(
            header='🔎 Окей, начинаю поиск',
            description='Я пришлю Вам подходящий контент, ожидайте.⏱',
            btn_text=OK_THANKS
        )
        return render(request, template_name=SUCCESS_TEMPLATE_PATH, context=context)


class SearchCustomChannels(View):
    """
    Вьюшки для поиска собственных телеграм каналов.
    """

    def get(self, request):
        MY_LOGGER.info('GET запрос на вьюшку SearchNewChannels')
        return render(request, template_name='mytlg/search_custom_channels.html')

    def post(self, request):
        MY_LOGGER.info('Поступил POST запрос на вьюшку для поиска телеграм канала')

        form = SearchAndAddNewChannelsForm(request.POST)
        if not form.is_valid():
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors}')
            err_msgs.error(request, 'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('mytlg:search_custom_channels'))
        tlg_id = form.cleaned_data.get("tlg_id")
        search_keywords = form.cleaned_data.get('search_keywords')

        # Получаем найденные каналы и передаем пользователю результаты
        account_for_search_pk = TlgAccountsService.get_tlg_account_id_for_search_custom_channels()
        channel_for_subscrbe_form, founded_channels = ChannelsService.send_request_for_search_channels(search_keywords,
                                                                                                       account_for_search_pk=account_for_search_pk,
                                                                                                       results_limit=5)

        subscribe_form = SubscribeChannelForm(initial={'tlg_id': tlg_id})
        subscribe_form.fields['channels_for_subscribe'].choices = channel_for_subscrbe_form
        cache.set(f'{tlg_id}-CHANNELS_FOR_FORM_CHOICES', channel_for_subscrbe_form, timeout=3600)
        cache.set(f'{tlg_id}-CHANNEL_DATA_FOR_SUBSCRIBE', founded_channels, timeout=3600)
        context = dict(
            form=subscribe_form,
            channels_list=founded_channels,
            search_keywords=search_keywords
        )
        return render(request, CHANNEL_SEARCH_RESULTS_TEMPLATE_PATH, context)


class SubscribeCustomChannels(View):
    """
    Вьюшки для обработки формы добавления собственных телеграм каналов.
    """

    def get(self, request):
        MY_LOGGER.info('GET запрос на вьюшку SubscribeNewChannels')
        return render(request, template_name='mytlg/channels_search_results.html')

    def post(self, request):
        MY_LOGGER.info(f'{request.POST} Поступил POST запрос на вьюшку для подписки на собственные телеграм каналы')
        form = SubscribeChannelForm(request.POST)
        tlg_id = request.POST.get("tlg_id")
        # MY_LOGGER.info(f'Каналы для формы подписки {CHANNELS_FOR_FORM_CHOICES}')
        # MY_LOGGER.info(f'Каналы для подписки {CHANNEL_DATA_FOR_SUBSCIBE}')
        form.fields['channels_for_subscribe'].choices = cache.get(f'{tlg_id}-CHANNELS_FOR_FORM_CHOICES')
        if not form.is_valid():
            MY_LOGGER.warning(f'Форма невалидна. Ошибка: {form.errors}')
            err_msgs.error(request, 'Ошибка: Вы уверены, что открыли форму из Telegram?')
            return redirect(to=reverse_lazy('mytlg:subscribe_custom_channels'))
        founded_channels = form.cleaned_data.get('channels_for_subscribe')

        # Проверяем каналы на подписку и блэклист и формируем список для отправки задачи на подписку
        channels_for_subscribe = [
            channel_id
            for channel_id in founded_channels
            if ChannelsService.check_channel_before_subscribe(channel_id)
        ]
        founded_channels_data = cache.get(f'{tlg_id}-CHANNEL_DATA_FOR_SUBSCRIBE')
        channels_data = [channel for channel in founded_channels_data if
                         str(channel.get('channel_id')) in channels_for_subscribe]
        # Создаем найденые каналы в админке
        new_channels = ChannelsService.create_founded_channels(channels_data)

        # Получаем телеграм аккаунт который будет использоваться для подписки на собственные каналы пользователя
        max_ch_per_acc = int(BotSettingsService.get_bot_settings_by_key(key='max_channels_per_acc'))
        tlg_account = TlgAccountsService.get_tlg_account_for_subscribe_custom_channels(max_ch_per_acc,
                                                                                       len(channels_data))

        # TODO создать задачу на подписку
        try:
            subs_task = AccountsSubscriptionTasksService.create_subscription_task(tlg_account, new_channels)

            MY_LOGGER.info('Отправляем задачу на подписку на собственные каналы')
            ChannelsService.send_command_to_accounts_for_subscribe_channels(channels_for_subscribe=channels_data,
                                                                            account_pk_for_subscribe=tlg_account.pk,
                                                                            subs_task_pk=subs_task.pk
                                                                            )
            return HttpResponse('<p>Ok</p>')
        except Exception as e:
            MY_LOGGER.warning(f'Ошибка при создании задачу на подписку на собственные каналы {e}')

            return HttpResponse(f'<p>Ошибка при создании задачу на подписку на собственные каналы {e}</p>')
