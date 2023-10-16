from mytlg.models import Interests
import datetime


class InterestsService:

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
