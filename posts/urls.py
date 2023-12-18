from django.urls import path

from posts.views import RawChannelPost

app_name = 'posts'
urlpatterns = [
    path('raw_channel_post/', RawChannelPost.as_view(), name='raw_channel_post'),
]