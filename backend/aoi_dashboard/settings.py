import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-aoi-process-dashboard-development-key",
)
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174",
    ).split(",")
    if origin.strip()
]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

ROOT_URLCONF = "aoi_dashboard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "static"],
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

WSGI_APPLICATION = "aoi_dashboard.wsgi.application"


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required when Oracle mode is enabled.")
    return value


AOI_USE_MOCK_DATA = os.getenv("AOI_USE_MOCK_DATA", "true").lower() == "true"
AOI_SOURCE_DB_SCHEMA = os.getenv("AOI_SOURCE_DB_SCHEMA", "OFCSEUC").strip().upper()
database_mode = os.getenv("DJANGO_DATABASE", "sqlite" if AOI_USE_MOCK_DATA else "oracle").lower()

if database_mode == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    oracle_client_dir = os.getenv("ORACLE_CLIENT_LIB_DIR")
    if oracle_client_dir:
        try:
            import cx_Oracle

            cx_Oracle.init_oracle_client(lib_dir=oracle_client_dir)
        except ImportError:
            import oracledb

            oracledb.init_oracle_client(lib_dir=oracle_client_dir)

    oracle_dsn = os.getenv("ORACLE_DSN", "").strip()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.oracle",
            "NAME": oracle_dsn or required_env("ORACLE_SERVICE_NAME"),
            "USER": required_env("ORACLE_USER"),
            "PASSWORD": required_env("ORACLE_PASSWORD"),
            "HOST": "" if oracle_dsn else required_env("ORACLE_HOST"),
            "PORT": "" if oracle_dsn else os.getenv("ORACLE_PORT", "1521"),
        }
    }

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = False

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]
}
