# -*- coding: utf-8 -*-
from .com import *  # noqa

DATABASES = {
    'default': env.db('PRODB_URL', default='postgres://postgres:123456@127.0.0.1:5432/jasmin_webdb')
}

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

INSTALLED_APPS += ("gunicorn",)

DJANGO_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", default="WARNING")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': DJANGO_LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(str(ROOT_DIR), 'logs/app.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'standard',
        },
        'request_handler': {
            'level': DJANGO_LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(str(ROOT_DIR), 'logs/django.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': True
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False
        },
    }
}
