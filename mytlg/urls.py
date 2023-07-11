from django.urls import path

from mytlg.views import StartSettingsView, save_themes_view, WriteUsrView, WriteInterestsView, text_view

app_name = 'mytlg'

urlpatterns = [
    path('start_settings/', StartSettingsView.as_view(), name='start_settings'),
    path('save_themes/', save_themes_view, name='save_themes'),
    path('write_usr/', WriteUsrView.as_view(), name='write_usr'),
    path('write_interests/', WriteInterestsView.as_view(), name='write_interests'),

    path('test/', text_view, name='test'),
]
