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
    Форма для функции "что было нового".
    """
    search_keywords = forms.CharField()
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])
