# -*- coding: utf-8 -*-
from .com import *  # noqa

DATABASES = {
    'default': env.db('PRODB_URL', default='postgres://postgres:123456@127.0.0.1:5432/jasmin_webdb')
}

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Set HTTPS_ONLY=True when the panel is served over HTTPS (directly or behind a TLS-terminating
# proxy that sets X-Forwarded-Proto). Off by default so plain-HTTP intranet installs keep working.
HTTPS_ONLY = env.bool('HTTPS_ONLY', default=False)
if HTTPS_ONLY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    # Container and Kubernetes health checks call this over plain HTTP from inside the pod.
    SECURE_REDIRECT_EXEMPT = [r'^api/health_check$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)

# Keys published in this repository (code default and sample.env): anyone can forge sessions with them.
if SECRET_KEY in ('change-me', '8na#(#x@0i*3ah%&$-q)b&wqu5ct_a3))d8-sqk-ux*5lol*wl',
                  '8na#(#x@0i*3ah%&$-q)b&wqu5ct_a3))d8-sqk-ux*5*lolwb'):
    import warnings
    warnings.warn('SECRET_KEY is the public sample value; set a long random SECRET_KEY in .env', RuntimeWarning)

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
