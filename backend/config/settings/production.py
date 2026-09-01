from decouple import Csv, config
from .base import *

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST"),
        "PORT": config("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 600,
    }
}

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
