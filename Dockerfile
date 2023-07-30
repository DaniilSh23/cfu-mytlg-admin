FROM python:3.10-slim

RUN mkdir "django_app"

COPY requirements.txt /django_app/

RUN python -m pip install -r /django_app/requirements.txt

COPY cfu_mytlg_admin /django_app/
COPY media /django_app/
COPY mytlg /django_app/
COPY static /django_app/
COPY .env /django_app/
COPY manage.py /django_app/

WORKDIR /django_app

# Открываем 8000 и 6379 порты для Gunicorn и Redis
EXPOSE 8000

# Запуск Celery и Gunicorn
CMD celery -A cfu_mytlg_admin worker --loglevel=info -B & gunicorn cfu_mytlg_admin.wsgi:application --bind 0.0.0.0:8000

