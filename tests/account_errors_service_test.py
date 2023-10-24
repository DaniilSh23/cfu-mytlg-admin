from django.test import TestCase
from mytlg.models import TlgAccounts, AccountsErrors, Proxys
from mytlg.servises.account_errors_service import TlgAccountErrorService
from mytlg.serializers import AccountErrorSerializer


class TlgAccountErrorServiceTest(TestCase):

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

    def test_create_tlg_account_error(self):

        # Create a test serializer with the necessary data
        serializer = AccountErrorSerializer()
        serializer._validated_data = {
            "error_type": "Test Error",
            "error_description": "This is a test error.",
        }

        # Call the create_tlg_account_error method
        TlgAccountErrorService.create_tlg_account_error(serializer, self.test_account)

        # Retrieve the created error object
        error = AccountsErrors.objects.get(account=self.test_account)

        # Check if the error object is created with the correct data
        self.assertEqual(error.error_type, "Test Error")
        self.assertEqual(error.error_description, "This is a test error.")

        # Check that the error is associated with the correct TlgAccount
        self.assertEqual(error.account, self.test_account)
