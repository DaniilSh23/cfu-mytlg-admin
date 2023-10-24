from mytlg.models import Interests
import datetime
import pytz
from cfu_mytlg_admin.settings import MY_LOGGER, TIME_ZONE
from mytlg.utils import calculate_sending_datetime


class InterestsService:

    @staticmethod
    def create(bot_user_obj, category, embedding_str, interest):
        new_interest = Interests.objects.create(
            interest=interest,
            embedding=embedding_str,
            bot_user=bot_user_obj,
            category=category,
            is_active=False,
            send_period='now',
            interest_type='whats_new',
        )
        MY_LOGGER.success(f'В БД создан новый интерес юзера {bot_user_obj!r} | PK интереса == {new_interest.pk!r}')
        return new_interest

    @staticmethod
    def get_active_interests(bot_user):
        return (Interests.objects.filter(bot_user=bot_user, is_active=True, interest_type='main')
                .only('pk', 'is_active'))

    @staticmethod
    def set_is_active_false_in_active_interests(active_interests):
        for interest in active_interests:
            interest.is_active = False
            interest.save()

    @staticmethod
    def create_list_of_new_interests_obj(interests_indxs, request):
        return [
            dict(
                interest=request.POST.get(f"interest{indx + 1}"),
                send_period=request.POST.get(f"send_period{indx + 1}"),
                when_send=datetime.datetime.strptime(
                    request.POST.get(f"when_send{indx + 1}")[:5], '%H:%M'
                ).time()
                if request.POST.get(f"when_send{indx + 1}")
                else None,
                last_send=datetime.datetime.now(),
            )
            for indx in interests_indxs
        ]

    @staticmethod
    def check_for_having_interests(interests_examples, request):
        return [
            i
            for i in range(len(interests_examples))
            if request.POST.get(f"interest{i + 1}") != ''
        ]

    @staticmethod
    def get_send_periods():
        return Interests.periods

    @staticmethod
    def check_if_bot_user_have_interest(bot_user_pk: int) -> bool:
        return bool(Interests.objects.filter(bot_user__pk=bot_user_pk))

    # TODO тест для метода
    @staticmethod
    def filter_interest_for_scheduling_posts(i_user, interest, post):
        return (
            Interests.objects.filter(category=post.channel.category, bot_user=i_user, is_active=True,
                                     interest_type='main')
            .only('id', 'interest', 'embedding', 'when_send')
        ) if not interest else (interest,)

    @staticmethod
    def calculate_sending_time_for_interest(filtered_rel_pieces, i_user, interest, interests):
        sending_datetime = None
        interest = interests[0]
        for i_interest in interests:
            if filtered_rel_pieces[0][0].page_content == i_interest.interest:
                MY_LOGGER.debug(f'Найден релевантный интерес у юзера {i_user.pk!r} | {i_interest.interest!r} | '
                                f'Векторное расстояние: {filtered_rel_pieces[0][1]}')
                # Рассчитываем время предстоящей отправки
                sending_datetime = calculate_sending_datetime(
                    last_send=i_interest.last_send,
                    send_period=i_interest.send_period,
                    when_send=i_interest.when_send,
                )
                interest = i_interest
                break
        return interest, sending_datetime

    @staticmethod
    def create_interests_list(interests):
        interest_lst = [
            (i_interest.interest, [float(i_emb) for i_emb in i_interest.embedding.split()])
            for i_interest in interests
        ]
        return interest_lst

    @staticmethod
    def bulk_create_interests(bot_usr, interests):
        interests_objs = []
        for interest in interests:
            interest['bot_user'] = bot_usr
            interests_objs.append(Interests(**interest))
        Interests.objects.bulk_create(interests_objs)

    @staticmethod
    def update_date_and_time_interests_last_sending_time(interests_ids):
        Interests.objects.filter(id__in=set(interests_ids)).update(
            last_send=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE))
        )
