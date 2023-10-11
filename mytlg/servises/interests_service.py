from mytlg.models import Interests


class InterestsService:

    @staticmethod
    def get_active_interests(bot_user):
        active_interests = (Interests.objects.filter(bot_user=bot_user, is_active=True, interest_type='main')
                            .only('pk', 'is_active'))
        return active_interests

    @staticmethod
    def set_is_active_false_in_active_interests(active_interests):
        active_interests.update(is_active=False)
