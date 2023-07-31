FROM python:3.10-slim

RUN mkdir "django_app"

COPY requirements.txt /django_app/

RUN apt update

RUN apt install python3-dev libpq-dev postgresql-contrib curl -y

RUN apt-get install build-essential -y

RUN pip install psycopg2-binary

RUN python -m pip install --no-cache-dir -r /django_app/requirements.txt

COPY . /django_app/

WORKDIR /django_app

RUN python manage.py migrate

# Открываем 8000 и 6379 порты для Gunicorn и Redis
EXPOSE 8000

# Запуск Celery и Gunicorn
CMD ["celery", "-A", "cfu_mytlg_admin", "worker", "--loglevel=info", "-B", "&", "gunicorn", "--bind", "0.0.0.0:8000", "cfu_mytlg_admin.wsgi:application"]

