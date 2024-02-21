from django.test import TestCase
from django.test import RequestFactory
from user_interface.models import Interests
from mytlg.models import BotUser
from mytlg.models import Categories
from mytlg.servises.interests_service import InterestsService
import datetime


class InterestsServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.factory = RequestFactory()
        cls.bot_user = BotUser.objects.create(
            tlg_id="123456789",
            tlg_username="user_name",
            language_code="ru",
        )

        cls.category = Categories.objects.create(category_name="test")
        cls.interest1 = Interests.objects.create(bot_user=cls.bot_user, is_active=True, interest_type='main',
                                                 category_id=cls.category.id)
        cls.interest2 = Interests.objects.create(bot_user=cls.bot_user, is_active=True, interest_type='main',
                                                 category_id=cls.category.id)

    def test_get_active_interests(self):
        InterestsService.set_is_active_false_in_active_interests([self.interest2])
        # Call the method being tested
        active_interests = InterestsService.get_active_interests(self.bot_user)
        # Check if the method returns the active interests
        self.assertEqual(list(active_interests), [self.interest1])

    def test_set_is_active_false_in_active_interests(self):
        # Create some Interests objects related to the bot_user (modify as needed)
        interest1 = Interests.objects.create(bot_user=self.bot_user, is_active=True, interest_type='main',
                                             category_id=self.category.id)
        interest2 = Interests.objects.create(bot_user=self.bot_user, is_active=True, interest_type='main',
                                             category_id=self.category.id)

        # Call the method being tested
        InterestsService.set_is_active_false_in_active_interests([interest1, interest2])

        # Check if the interests were updated to is_active=False
        self.assertEqual(Interests.objects.filter(is_active=False).count(), 2)

    def test_create_list_of_new_interests_obj(self):
        # Create a request object for testing
        request = self.factory.post('/', data={
            'interest1': 'Interest 1',
            'send_period1': 'Daily',
            'when_send1': '12:00',
            'interest2': 'Interest 2',
            'send_period2': 'Weekly',
            'when_send2': '08:30',
        })

        # Call the method being tested
        new_interests_objs = InterestsService.create_list_of_new_interests_obj([0, 1], request)

        # Check if the method creates new interest objects
        self.assertEqual(len(new_interests_objs), 2)
        self.assertEqual(new_interests_objs[0]['interest'], 'Interest 1')
        self.assertEqual(new_interests_objs[0]['send_period'], 'Daily')
        self.assertEqual(new_interests_objs[0]['when_send'], datetime.time(12, 0))
        self.assertIsNotNone(new_interests_objs[0]['last_send'])
        self.assertEqual(new_interests_objs[1]['interest'], 'Interest 2')
        self.assertEqual(new_interests_objs[1]['send_period'], 'Weekly')
        self.assertEqual(new_interests_objs[1]['when_send'], datetime.time(8, 30))
        self.assertIsNotNone(new_interests_objs[1]['last_send'])

    def test_check_for_having_interests(self):
        # Create a request object for testing
        request = self.factory.post('/', data={
            'interest1': 'Interest 1',
            'interest2': '',  # This interest is empty
            'interest3': 'Interest 3',
        })

        # Call the method being tested
        interests_indxs = InterestsService.check_for_having_interests(['interest1', 'interest2', 'interest3'], request)

        # Check if the method correctly identifies the indices of non-empty interests
        self.assertEqual(interests_indxs, [0, 2])

    def test_get_send_periods(self):
        send_periods = InterestsService.get_send_periods()

        # Check if the method returns the expected send periods
        self.assertEqual(send_periods, Interests.periods)

    def test_check_if_bot_user_have_interest(self):
        self.assertTrue(InterestsService.check_if_bot_user_have_interest(self.bot_user.pk))


    # def test_bulk_create_interests(self):
    #     interests = [self.interest1, self.interest2]
    #     InterestsService.bulk_create_interests(self.bot_user, interests)
    #     interests_count = Interests.objects.filter(bot_user=self.bot_user).count()
    #     self.assertEqual(interests_count, 2)

    def test_update_date_and_time_interests_last_sending_time(self):
        interests = Interests.objects.create(bot_user=self.bot_user, category_id=self.category.id)
        InterestsService.update_date_and_time_interests_last_sending_time([interests.id])
        updated_interest = Interests.objects.get(pk=interests.id)
        self.assertGreater(updated_interest.last_send, interests.last_send)
