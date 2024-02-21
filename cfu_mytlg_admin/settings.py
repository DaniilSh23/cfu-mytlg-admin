"""
Django settings for cfu_mytlg_admin project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import sys
from pathlib import Path
import environ

import loguru
from celery.schedules import crontab

# Это отсюда https://django-environ.readthedocs.io/en/latest/quickstart.html
env = environ.Env(
    # set casting, default value
    DEBUG=bool,  # Для переменной DEBUG указываем тип данных, когда достаём из .env
    SECRET_KEY=str,
    DOMAIN_NAME=str,
    REDIS_HOST=str,
    REDIS_PORT=str,
    DATABASE_NAME=str,
    DATABASE_USER=str,
    DATABASE_PASSWORD=str,
    DATABASE_HOST=str,
    DATABASE_PORT=str,
    TG_API_ID=str,
    TG_API_HASH=str,
    BOT_TOKEN=str,
    OPENAI_KEY=str,
    SEND_NEWS_TIMEOUT=int,
    SHOW_SQL_LOG=bool,
    SENTRY_DSN=str,
    ACCOUNT_SERVICE_HOST=str,
    OPEN_AI_APP_TOKEN=str,
    OPEN_AI_SERVICE_HOST=str,
    BOT_LINK=str,
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
# Это отсюда https://django-environ.readthedocs.io/en/latest/quickstart.html
environ.Env.read_env(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']
DOMAIN_NAME = env('DOMAIN_NAME')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Созданные приложения
    'mytlg.apps.MytlgConfig',
    'posts.apps.PostsConfig',
    'telegram_accounts.apps.TelegramAccountsConfig',
    'support.apps.SupportConfig',
    'user_interface.apps.UserInterfaceConfig',

    # сторонние приложения
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cfu_mytlg_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cfu_mytlg_admin.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# REST FRAMEWORK settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

# DRF SPECTACULAR settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'YourTelegram API',
    'DESCRIPTION': 'API for YourTelegram Project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
if DEBUG:
    STATICFILES_DIRS = (
        BASE_DIR / 'static',
    )
else:
    STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = '/media/'  # путь в адресной строке для получения медиа-файлов
MEDIA_ROOT = BASE_DIR / 'media'  # путь к медиа-файлам на диске

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery settings
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"  # Это адрес брокера сообщений (у нас Redis)
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}"  # Это адрес бэкэнда результатов (тоже у нас Redis)
CELERY_TIMEZONE = "Europe/Moscow"  # Временная зона для Celery
CELERY_BEAT_SCHEDULE = {  # Настройки шедуля
    'sending_post_selections': {
        'task': 'mytlg.tasks.sending_post_selections',
        'schedule': 120,
    },
    'what_was_interesting': {
        'task': 'mytlg.tasks.what_was_interesting',
        'schedule': crontab(hour=11, minute=30, day_of_week=1),  # Запуск в понедельник в 11:30
        # 'schedule': 10,  # Каждые 10 сек
    },
    'sending_channels_report': {
        "task": "mytlg.tasks.sending_channels_report",
        "schedule": crontab(hour="10, 14, 18", minute=0)
    }
}

# Настройки логгера
MY_LOGGER = loguru.logger
MY_LOGGER.remove()  # Удаляем все предыдущие обработчики логов
MY_LOGGER.add(sink=sys.stdout, level='DEBUG')  # Все логи от DEBUG и выше в stdout
MY_LOGGER.add(  # системные логи в файл
    sink=f'{BASE_DIR}/logs/sys_log.log',
    level='DEBUG',
    rotation='2 MB',
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True
)

# Настройки для Telegram
BOT_TOKEN = env('BOT_TOKEN')

# Сервис управления аккаунтами
ACCOUNT_SERVICE_HOST = env('ACCOUNT_SERVICE_HOST')
DEL_ACCOUNT_URL = f"{ACCOUNT_SERVICE_HOST}del_acc/"
START_SUBSCRIPTION_ULR = f"{ACCOUNT_SERVICE_HOST}subs_accs_to_channels/"
START_ACCOUNT_ULR = f"{ACCOUNT_SERVICE_HOST}start_acc/"
STOP_ACCOUNT_ULR = f"{ACCOUNT_SERVICE_HOST}stop_acc/"

# OpenAI Token
OPENAI_API_KEY = env('OPENAI_API_KEY')

# Настройки для проксирования запросов от Nginx при деплое через докер
CSRF_TRUSTED_ORIGINS = ['http://0.0.0.0:8000']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Настройка логирование запросов к БД
SHOW_SQL_LOG = env('SHOW_SQL_LOG')
if SHOW_SQL_LOG:
    LOGGING = {
        'version': 1,
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'filters': ['require_debug_true'],
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'level': 'DEBUG',
                'handlers': ['console'],
            },
        },
    }

# Настройка sentry для отлова ошибок
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SENTRY_DSN = env("SENTRY_DSN")
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

# Настройка Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379',  # Ваша конфигурация Redis
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CHANNELS_BLACK_LIST = []
OPEN_AI_APP_TOKEN = env('OPEN_AI_APP_TOKEN')
OPEN_AI_SERVICE_HOST = env('OPEN_AI_SERVICE_HOST')
BOT_LINK = env('BOT_LINK')
