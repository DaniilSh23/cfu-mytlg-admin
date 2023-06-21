from django.urls import path

from mytlg.views import StartSettingsView, save_themes_view, WriteUsrView

app_name = 'mytlg'

urlpatterns = [
    path('start_settings/', StartSettingsView.as_view(), name='start_settings'),
    path('save_themes/', save_themes_view, name='save_themes'),
    path('write_usr/', WriteUsrView.as_view(), name='write_usr'),
]
