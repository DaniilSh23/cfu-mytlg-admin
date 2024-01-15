from django import forms
from django.core.validators import RegexValidator


class JSONImportForm(forms.Form):
    """
    Форма для загрузки JSON файла в админке.
    """
    json_file = forms.FileField()


class BlackListForm(forms.Form):
    """
    Форма для ключевых слов черного списка.
    """
    keywords = forms.CharField()
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])


class WhatWasInterestingForm(forms.Form):
    """
    Форма для функции "что было нового".
    """
    interest = forms.CharField()
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])


class SearchAndAddNewChannelsForm(forms.Form):
    """
    Форма для ввода ключевых слов для поиска своих каналов.
    """
    search_keywords = forms.CharField()
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])


class SubscribeChannelForm(forms.Form):
    """
    Форма для подписки на найденные каналы".
    """
    channels_for_subscribe = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=''
    )
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )],
        widget=forms.TextInput(attrs={
            'class': 'my-filling-fields',
            'id': 'tg-id-input',
            'name': 'tg-id',
            'type': 'hidden'
        })
    )


class CustomChannelsSettingsForm(forms.Form):
    """
    Форма для настроек получения новостей из кастомных каналов пользователя.
    """
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])
    when_send = forms.TimeField()
    send_period = forms.CharField()
