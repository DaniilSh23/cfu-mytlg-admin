from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from mytlg.models import TlgAccounts, Proxys
from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.servises.tlg_accounts_service import TlgAccountsService


class TlgAccountsServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a test TlgAccounts instance for use in the tests
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

    def test_filter_and_update_tlg_account(self):
        updated_data = {
            "tlg_first_name": "Updated Name",
            "acc_tlg_id": '456'
        }
        updated_count = TlgAccountsService.filter_and_update_tlg_account(self.test_account.pk, updated_data)
        self.assertEqual(updated_count, 1)

        # Reload the instance from the database to check the updated values
        self.test_account.refresh_from_db()
        self.assertEqual(self.test_account.tlg_first_name, "Updated Name")
        self.assertEqual(self.test_account.acc_tlg_id, '456')

    def test_get_tlg_account_by_pk_existing(self):
        account = self.test_account
        self.assertEqual(account.tlg_first_name, "Test Account")
        self.assertEqual(account.acc_tlg_id, '123')

    def test_get_tlg_account_by_pk_non_existing(self):
        account = TlgAccountsService.get_tlg_account_by_pk(999)  # Non-existing PK
        self.assertIsNone(account)

    def test_get_tlg_account_only_id_by_pk_existing(self):
        account_id = TlgAccountsService.get_tlg_account_only_id_by_pk(self.test_account.pk)
        self.assertEqual(account_id.id, self.test_account.id)

    def test_get_tlg_account_only_id_by_pk_non_existing(self):
        account_id = TlgAccountsService.get_tlg_account_only_id_by_pk(999)  # Non-existing PK
        self.assertIsNone(account_id)
