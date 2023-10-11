from mytlg.models import Interests
import datetime


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
