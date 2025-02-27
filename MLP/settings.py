"""
Django settings for MLP project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import structlog
from firebase_admin import initialize_app
from firebase_admin import credentials


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR,".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-sile&1t1giixu+yldl_rzzlfah=+@$k__qr8&woq-&ljo=967e'

# SECURITY WARNING: don't run with debug turned on in production!
ENV = os.getenv("ENV","dev")
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'users',
    'search',
    'transactions',
    'promotions',
    'misc',
    'rest_framework',
    'rangefilter',
    'django_crontab',
    'notification_settings'
]

ASGI_APPLICATION = "MLP.asgi.application"

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CRONJOBS = [
    ("30 18 * * *", "cronjob.main.main_cronjob", ">> " + os.path.join(BASE_DIR, "log/cron.log" + " 2>&1 "))
]

# settings.py or celery.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_IMPORTS = ("misc.service",)

CORS_ORIGIN_ALLOW_ALL = True

CSRF_TRUSTED_ORIGINS = ['https://dev.medicolifepartner.com', 'http://localhost:8000']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.ap-south-1.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('SMTP_USERNAME')      # Must create SMTP Credentials
EMAIL_HOST_PASSWORD = os.getenv('SMTP_PASSWORD')  # Must create SMTP Credentials

ROOT_URLCONF = 'MLP.urls'

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

WSGI_APPLICATION = 'MLP.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
} if DEBUG else {
  'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'medico',
        'PASSWORD': 'medicoPass',
        'HOST': 'medico-devdb.caafifb3tu2f.ap-south-1.rds.amazonaws.com',
        'PORT': '5432',

        # 'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': 'medico',
        # 'USER': 'medico',
        # 'PASSWORD': 'medicoPass',
        # 'HOST': 'localhost',
        # 'PORT': '5432',
   }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_CONNECTION_URL"),  # Adjust accordingly
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}



# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/


STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
credentials_path = os.path.join(BASE_DIR,"service-account-file.json")
cred = credentials.Certificate(credentials_path)
FIREBASE_APP = initialize_app(cred)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        'error_formatter': {
            'format': '{asctime} - {levelname} - "{pathname}" - {funcName}: {message}',
            'style': '{',
        },
        'transaction_formatter': {
            'format': '{asctime}: {message}',
            'style': '{',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain_console",
        },
        "error_logger":{
            "class": "logging.handlers.WatchedFileHandler",
            "filename": os.path.join(BASE_DIR, "log/errors.log"),
            "level": "ERROR",
            "formatter":"error_formatter"
        },
        "transactional_logger":{
            "class": "logging.handlers.WatchedFileHandler",
            "filename": os.path.join(BASE_DIR, "log/transactions.log"),
            "level": "INFO",
            "formatter":"transaction_formatter"
        },
    },
    "loggers": {
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "error_logger": {
            "handlers": ["console", "error_logger"],
            "level": "ERROR",
        },
        "transactional_logger": {
            "handlers": ["console", "transactional_logger"],
            "level": "INFO",
        },
        "django_structlog_demo_project": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
}
