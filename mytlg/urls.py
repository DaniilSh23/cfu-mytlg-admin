from django.urls import path

from mytlg.views import WriteUsrView, WriteInterestsView, \
    GetChannelsListView, RelatedNewsView, UploadNewChannels, WriteSubsResults, UpdateChannelsView, GetActiveAccounts, \
    AccountError, SetAccFlags, BlackListView, WhatWasInteresting, ShowScheduledPosts, SentReactionHandler, \
    SearchCustomChannels, SubscribeCustomChannels, InterestsSetting

app_name = 'mytlg'

urlpatterns = [
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
    path('black_list/', BlackListView.as_view(), name='black_list'),
    path('what_was_interesting/', WhatWasInteresting.as_view(), name='what_was_interesting'),
    path('show_scheduled_posts/', ShowScheduledPosts.as_view(), name='show_scheduled_posts'),
    path('sent_reaction/', SentReactionHandler.as_view(), name='sent_reaction'),
    path('search_custom_channels/', SearchCustomChannels.as_view(), name='search_custom_channels'),
    path('subscribe_custom_channels/', SubscribeCustomChannels.as_view(), name='subscribe_custom_channels'),
    path('interests_setting/', InterestsSetting.as_view(), name='interests_setting'),
]

