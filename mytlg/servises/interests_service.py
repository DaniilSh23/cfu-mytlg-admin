from mytlg.models import Interests
import datetime
from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.utils import calculate_sending_datetime


class InterestsService:

    @staticmethod
    def get_active_interests(bot_user):
        active_interests = (Interests.objects.filter(bot_user=bot_user, is_active=True, interest_type='main')
                            .only('pk', 'is_active'))
        return active_interests

    @staticmethod
    def set_is_active_false_in_active_interests(active_interests):
        active_interests.update(is_active=False)

    @staticmethod
    def create_list_of_new_interests_obj(interests_indxs, request):
        new_interests_objs = [
            dict(
                interest=request.POST.get(f"interest{indx + 1}"),
                send_period=request.POST.get(f"send_period{indx + 1}"),
                when_send=datetime.datetime.strptime(request.POST.get(f"when_send{indx + 1}")[:5], '%H:%M').time()
                if request.POST.get(f"when_send{indx + 1}") else None,
                last_send=datetime.datetime.now(),
            )
            for indx in interests_indxs
        ]
        return new_interests_objs

    @staticmethod
    def check_for_having_interests(interests_examples, request):
        interests_indxs = []
        for i in range(len(interests_examples)):
            if request.POST.get(f"interest{i + 1}") != '':
                interests_indxs.append(i)
        return interests_indxs

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
