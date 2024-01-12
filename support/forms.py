from django import forms
from django.core.validators import RegexValidator


class SupportMessageForm(forms.Form):
    """
    Форма для ввода ключевых слов для поиска своих каналов.
    """
    message = forms.Textarea()
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])
