from django.urls import path

from mytlg.views import StartSettingsView, WriteUsrView, WriteInterestsView, test_view

app_name = 'mytlg'

urlpatterns = [
    path('start_settings/', StartSettingsView.as_view(), name='start_settings'),
    path('write_usr/', WriteUsrView.as_view(), name='write_usr'),
    path('write_interests/', WriteInterestsView.as_view(), name='write_interests'),

    path('test/', test_view, name='test'),
]
