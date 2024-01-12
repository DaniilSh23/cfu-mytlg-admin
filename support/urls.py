from django.urls import path

from support.views import SupportMessages

app_name = 'support'

urlpatterns = [
    path('give_support_message/', SupportMessages.as_view(), name='give_support_message'),
]