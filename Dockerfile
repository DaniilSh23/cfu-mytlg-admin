FROM python:3.10-slim

RUN mkdir "cfu_mytlg_admin"

COPY requirements.txt /cfu_mytlg_admin/

RUN apt update

RUN apt install python3-dev libpq-dev postgresql-contrib curl -y

RUN apt-get install build-essential -y

RUN pip install psycopg2-binary

RUN python -m pip install --no-cache-dir -r /cfu_mytlg_admin/requirements.txt

COPY . /cfu_mytlg_admin/

WORKDIR /cfu_mytlg_admin

# Ниже команды для создания суперпользователя в Django
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_PASSWORD=admin
ENV DJANGO_SUPERUSER_EMAIL=my@dmin.com

# Открываем 8000 порт
EXPOSE 8000

# Запуск
ENTRYPOINT ["/cfu_mytlg_admin/entrypoint.sh"]