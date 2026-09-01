import os
from .base import *

DEBUG = True

# Database Configuration: PostgreSQL + PostGIS with SQLite fallback for offline unit tests
DB_ENGINE = config("DB_ENGINE", default="django.db.backends.postgresql")
DB_NAME = config("POSTGRES_DB", default="idr_backend")
DB_USER = config("POSTGRES_USER", default="postgres")
DB_PASSWORD = config("POSTGRES_PASSWORD", default="postgres")
DB_HOST = config("POSTGRES_HOST", default="127.0.0.1")
DB_PORT = config("POSTGRES_PORT", default="5433")

USE_SQLITE_TEST = config("USE_SQLITE_TEST", default=False, cast=bool)

if USE_SQLITE_TEST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
        }
    }

# Handle GDAL availability on Windows Host OS when running outside container
try:
    from django.contrib.gis.gdal import libgdal
except Exception:
    if "django.contrib.gis" in INSTALLED_APPS:
        INSTALLED_APPS.remove("django.contrib.gis")
