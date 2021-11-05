"""Django 3.0.5"""
from __future__ import absolute_import, unicode_literals
from django.utils.translation import gettext_lazy as _
import os, environ

ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path('main')
CONF_DIR = ROOT_DIR.path('config')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
env.read_env('.env')

SECRET_KEY = env("SECRET_KEY", default='8na#(#x@0i*3ah%&$-q)b&wqu5ct_a3))d8-sqk-ux*5lol*wl')

DEBUG = env.bool("DEBUG", False)

SITE_ID = int(env("SITE_ID", default='1'))

INSTALLED_APPS = [
    'jet.dashboard',
    'jet',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # 'channels',
    'crequest',
    'rest_framework',

    'main.core',
    'main.taskapp',
    'main.users',
    'main.web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crequest.middleware.CrequestMiddleware',
    'main.core.middleware.TelnetConnectionMiddleware',
    'main.core.middleware.UserAgentMiddleware',
    'main.users.middleware.LastUserActivityMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(APPS_DIR.path('templates')),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.core.context_processors.site',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

WSGI_APPLICATION = 'config.wsgi.application'

ROOT_URLCONF = 'config.urls'

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = (
    'main.users.backends.UserModelBackend',
)

LOGIN_URL = "/account/login/"

ADMIN_URL = env('ADMIN_URL', default="admin/")

LOCALE_PATHS = (str(APPS_DIR('locale')), str(CONF_DIR('locale')),)

LANGUAGE_CODE = env('LANGUAGE_CODE', default="en")

LANGUAGES = (
    ('en', _('English')),
    ('tr', _('Türkçe')),
)

TIME_ZONE = env('TIME_ZONE', default='UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_TITLE  = "Jasmin Web site admin"
SITE_HEADER = "Jasmin Web administration"
INDEX_TITLE = "Dashboard administration"

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'info',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

STATIC_ROOT = str(ROOT_DIR('public/static'))

STATIC_URL = '/static/'

STATICFILES_DIRS = (str(APPS_DIR.path('static', )),)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

MEDIA_ROOT = str(ROOT_DIR('public/media'))

MEDIA_URL = '/media/'

REDIS_URL = ('localhost', 6379) #env.str('REDIS_URL', default=('localhost', 6379))

# ASGI Settings

# ASGI_APPLICATION = "config.routing.application"
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [REDIS_URL,],
#         },
#     },
# }

DEFAULT_USER_AVATAR = STATIC_URL + "assets/img/user.png"
DEFAULT_USER_FOLDER = "users"
LAST_ACTIVITY_INTERVAL_SECS = 3600

# REST API Settings

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.CoreJSONRenderer',
        'rest_framework_swagger.renderers.SwaggerUIRenderer',
        'rest_framework_swagger.renderers.OpenAPIRenderer',
    ),
}

SWAGGER_SETTINGS = {
    'LOGIN_URL': 'rest_framework:login',
    'LOGOUT_URL': 'rest_framework:logout',
    'USE_SESSION_AUTH': True,
    'DOC_EXPANSION': 'list',
    'APIS_SORTER': 'alpha',
    'SHOW_REQUEST_HEADERS': True,
}

# Jasmin Settings
"""Jasmin telnet defaults"""
TELNET_HOST = env('TELNET_HOST', default='127.0.0.1')
TELNET_PORT = env.int('TELNET_PORT', default=8990)
TELNET_USERNAME = env('TELNET_USERNAME', default='jcliadmin')
TELNET_PW = env('TELNET_PW', default='jclipwd')  # no alternative storing as plain text
TELNET_TIMEOUT = env.int('TELNET_TIMEOUT', default=10)  # reasonable value for intranet.

STANDARD_PROMPT = 'jcli : '  # There should be no need to change this
INTERACTIVE_PROMPT ='> '  # Prompt for interactive commands
SUBMIT_LOG = env.bool('SUBMIT_LOG', False)  # This is used for DLR Report


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
