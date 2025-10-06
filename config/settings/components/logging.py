import os

ENV = os.getenv("ENV", "dev").lower()           # dev | prod
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()

DEV_FMT  = "[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(message)s"
JSON_FMT = '{"ts":"%(asctime)s","lvl":"%(levelname)s","logger":"%(name)s",' \
           '"line":%(lineno)d,"msg":"%(message)s"}'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "dev":  {"format": DEV_FMT},
        "json": {"format": JSON_FMT},
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "dev" if ENV != "prod" else "json",
        },
    },

    "root": {"handlers": ["console"], "level": "WARNING"},

    "loggers": {
        "hubinsight": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},

        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},

        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
