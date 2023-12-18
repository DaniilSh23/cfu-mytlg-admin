from django.urls import path

from cfu_mytlg_admin.settings import DEBUG
from telegram_accounts.views import accounts_test_view, RunningAccountsView, SessionFilesView

app_name = 'telegram_accounts'

urlpatterns = [
    path('get_running_accounts/', RunningAccountsView.as_view(), name='get_running_accounts'),
    path('get_session_file/', SessionFilesView.as_view(), name='get_session_file'),
]

if DEBUG:
    urlpatterns.append(path('test/', accounts_test_view, name='test'))
