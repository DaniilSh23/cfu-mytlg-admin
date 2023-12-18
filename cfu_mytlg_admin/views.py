"""
Какие-нибудь "глобальные" вьюшки, которые нужны для всего проекта и не относятся к какому-либо приложению.
"""
from django.http import HttpRequest
from django.shortcuts import redirect

from cfu_mytlg_admin.settings import MY_LOGGER


def redirect_to_admin(request: HttpRequest):
    """
    Вьюшка для редиректа на страницу админки.
    """
    MY_LOGGER.info(f'Получен запрос на вьюшку для редиректа на страницу админки.')
    return redirect(to='/admin/')