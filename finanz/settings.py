import os
from typing import List

from django.conf.locale.de import formats as de_formats

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "!yz#260hqbx*yum@&70z+dpf4ryuyb!ibohfg-vy2*&6y*@-h("  # nosec: not used in production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: List[str] = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "bootstrap5",
    "bootstrap_datepicker_plus",
    "active_link",
    "django_crontab",
    "rechnung",
    "konto",
    "aufgaben",
    "schluessel",
    "getraenke",
    "common",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
]

ROOT_URLCONF = "finanz.urls"
LOGIN_URL = "login/"
LOGOUT_URL = "logout/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "finanz.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
    "getraenke": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "getraenke.sqlite3"),
    },
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # default, but important due to pickle

# Internationalization
LANGUAGE_CODE = "de-de"
LOCALE_NAME = "de"
TIME_ZONE = "Europe/Berlin"

USE_I18N = False
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

de_formats.DATETIME_FORMAT = "d.m.Y H:i:s"
de_formats.DATE_FORMAT = "d.m.Y"
de_formats.SHORT_DATE_FORMAT = "d.m."

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "node_modules"),
    os.path.join(BASE_DIR, "static"),
]

# Database stuff
DATABASE_ROUTERS = ["finanz.routers.DatabaseAppsRouter"]
DATABASE_APPS_MAPPING = {"getraenke": "getraenke"}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# cronjobs
CRONJOBS = [
    ("0 7 * * *", "common.cron.ueberfaellige_rechnung_reminder"),  # dayly at 07:00
    ("0 7 * * 1", "common.cron.zugewiesene_aufgabe_reminder"),  # weekly on modays at 7:00
]

# Media files (aufgaben.attachments, ...)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")
