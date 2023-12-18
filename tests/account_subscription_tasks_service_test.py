from django.test import TestCase
from mytlg.models import AccountsSubscriptionTasks, TlgAccounts, Proxys, Channels, Categories, BotSettings
from mytlg.servises.account_subscription_tasks_service import AccountsSubscriptionTasksService
from mytlg.serializers import WriteSubsResultSerializer
import datetime


class AccountsSubscriptionTasksServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.serializer = WriteSubsResultSerializer()
        proxy = Proxys.objects.create(
            description='описание',
            protocol_type=False,
            protocol='socks5',
            host='хост',
            port=65565,
            username='юзернейм',
            password='пароль',
            is_checked=True
        )

        cls.test_account = TlgAccounts.objects.create(
            tlg_first_name="Test Account",
            acc_tlg_id='123',
            session_file='sessions/pyro_447388296787.session',
            proxy=proxy,
        )

        cls.category = Categories.objects.create(
            category_name="Test Theme",
        )
        cls.test_channel = Channels.objects.create(
            channel_id=54321,
            channel_name="Test Channel",
            channel_link="https://test.com/channel",
            category=cls.category,
        )

    def test_get_account_subscription_tasks_by_pk(self):
        # Create a test AccountsSubscriptionTasks object
        test_task = AccountsSubscriptionTasks.objects.create(
            successful_subs=10,
            failed_subs=5,
            action_story="Test action story",
            status="Pending",
            ends_at=None,
            tlg_acc=self.test_account,
        )

        # Call the get_account_subscription_tasks_by_pk method
        task_obj = AccountsSubscriptionTasksService.get_account_subscription_tasks_by_pk(test_task.pk)

        # Check if the returned task object is the correct one
        self.assertEqual(task_obj, test_task)

    def test_get_account_subscription_tasks_by_pk_not_found(self):
        # Call the get_account_subscription_tasks_by_pk method with an unknown pk
        task = AccountsSubscriptionTasksService.get_account_subscription_tasks_by_pk(99999)  # Non-existing PK
        self.assertIsNone(task)

    def test_update_task_obj_data(self):
        # Create a test AccountsSubscriptionTasks object

        test_task = AccountsSubscriptionTasks.objects.create(
            successful_subs=10,
            failed_subs=5,
            action_story="Test action story",
            status="Pending",
            total_channels=10,
            started_at=datetime.datetime.now(),
            ends_at=datetime.datetime.now(),
            tlg_acc=self.test_account,
            initial_data='исходные данные',
        )

        # Create a dictionary of data to update the task
        serializer = self.serializer
        serializer._validated_data = {
            "success_subs": 5,
            "fail_subs": 2,
            "actions_story": "Updated action story",
            "status": "Completed",
            "end_flag": True
        }

        # Call the update_task_obj_data method
        AccountsSubscriptionTasksService.update_task_obj_data(serializer, test_task)

        # Check if the task object is updated correctly
        updated_task = AccountsSubscriptionTasks.objects.get(pk=test_task.pk)
        self.assertEqual(updated_task.successful_subs, 15)
        self.assertEqual(updated_task.failed_subs, 7)
        self.assertEqual(updated_task.action_story, "Updated action story\nTest action story")
        self.assertEqual(updated_task.status, "Completed")
        self.assertIsNotNone(updated_task.ends_at)

    def test_get_subscription_tasks_in_works(self):
        # Create a test TlgAccount and Channels with status 'at_work'

        BotSettings.objects.create(key='similarity_index_for_interests', value='0.8')

        # Create a test AccountsSubscriptionTasks with status 'at_work' and associated TlgAccount and Channels
        task = AccountsSubscriptionTasks.objects.create(
            successful_subs=10,
            failed_subs=5,
            action_story="Test action story",
            status="at_work",
            total_channels=10,
            started_at=datetime.datetime.now(),
            ends_at=datetime.datetime.now(),
            tlg_acc=self.test_account,
            initial_data='исходные данные',
        )
        task.channels.set([self.test_channel])

        # Call the method you want to test
        result = AccountsSubscriptionTasksService.get_subscription_tasks_in_works()
        # Assert that the expected task is in the result queryset
        self.assertIn(task, result)
