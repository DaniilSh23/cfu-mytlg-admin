from django.urls import path

from mytlg.views import StartSettingsView, WriteUsrView, WriteInterestsView, test_view, SetAccRunFlag, \
    GetChannelsListView, RelatedNewsView

app_name = 'mytlg'

urlpatterns = [
    path('start_settings/', StartSettingsView.as_view(), name='start_settings'),
    path('write_usr/', WriteUsrView.as_view(), name='write_usr'),
    path('write_interests/', WriteInterestsView.as_view(), name='write_interests'),
    path('set_acc_run_flag/', SetAccRunFlag.as_view(), name='set_acc_run_flag'),
    path('get_channels/', GetChannelsListView.as_view(), name='get_channels'),
    path('related_news/', RelatedNewsView.as_view(), name='related_news'),

    path('test/', test_view, name='test'),
]
