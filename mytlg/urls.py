from django.urls import path

from mytlg.views import StartSettingsView, WriteUsrView, WriteInterestsView, test_view, \
    GetChannelsListView, RelatedNewsView, UploadNewChannels, WriteSubsResults, UpdateChannelsView, GetActiveAccounts, \
    AccountError, SetAccFlags

app_name = 'mytlg'

urlpatterns = [
    path('start_settings/', StartSettingsView.as_view(), name='start_settings'),
    path('write_usr/', WriteUsrView.as_view(), name='write_usr'),
    path('write_interests/', WriteInterestsView.as_view(), name='write_interests'),
    # path('set_acc_run_flag/', SetAccRunFlag.as_view(), name='set_acc_run_flag'),
    path('set_acc_flags/', SetAccFlags.as_view(), name='set_acc_flags'),
    path('get_channels/', GetChannelsListView.as_view(), name='get_channels'),
    path('related_news/', RelatedNewsView.as_view(), name='related_news'),
    path('upload_new_channels/', UploadNewChannels.as_view(), name='upload_new_channels'),
    path('write_subs_rslt/', WriteSubsResults.as_view(), name='write_subs_rslt'),
    path('update_channels/', UpdateChannelsView.as_view(), name='update_channels'),
    path('get_active_accounts/', GetActiveAccounts.as_view(), name='get_active_accounts'),
    path('account_error/', AccountError.as_view(), name='account_error'),

    path('test/', test_view, name='test'),
]

