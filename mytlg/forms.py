from django import forms


class JSONImportForm(forms.Form):
    """
    Форма для загрузки JSON файла в админке.
    """
    json_file = forms.FileField()