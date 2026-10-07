from pathlib import Path
import os
from config import Config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = Config.SECRET_KEY
DEBUG = os.getenv("BMC_DJANGO_DEBUG", "1").lower() not in {"0", "false", "no"}
ALLOWED_HOSTS = Config.ALLOWED_HOSTS

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "console.apps.ConsoleConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "bmc_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    }
]

WSGI_APPLICATION = "bmc_server.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static_collected"
STATICFILES_DIRS = [BASE_DIR / "staticfiles"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ASGI_APPLICATION = "bmc_server.asgi.application"

TIME_ZONE = Config.TIMEZONE
USE_TZ = True

# Logging configuration
_console_level = os.getenv("BMC_LOG_CONSOLE_LEVEL", Config.LOG_CONSOLE_LEVEL)
_file_level = os.getenv("BMC_LOG_FILE_LEVEL", Config.LOG_FILE_LEVEL)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": _file_level,
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "logs" / "logs.log"),
            "formatter": "standard",
            "encoding": "utf-8",
            "mode": "a",
        },
        "console": {
            "level": _console_level,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["file", "console"],
    },
    "loggers": {
        "django": {
            "level": _console_level,
            "handlers": ["file", "console"],
            "propagate": False,
        },
    },
}

# Logging configuration - respects Config levels
_console_level = os.getenv("BMC_LOG_CONSOLE_LEVEL", Config.LOG_CONSOLE_LEVEL)
_file_level = os.getenv("BMC_LOG_FILE_LEVEL", Config.LOG_FILE_LEVEL)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": _file_level,
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "logs" / "logs.log"),
            "formatter": "standard",
            "encoding": "utf-8",
            "mode": "a",
        },
        "console": {
            "level": _console_level,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["file", "console"],
    },
    "loggers": {
        "django": {
            "level": _console_level,
            "handlers": ["file", "console"],
            "propagate": False,
        },
        "channels": {
            "level": _console_level,
            "handlers": ["file", "console"],
            "propagate": False,
        },
        "console": {
            "level": "DEBUG",
            "handlers": ["file", "console"],
            "propagate": False,
        },
    },
}
