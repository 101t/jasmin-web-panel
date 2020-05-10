# -*- coding: utf-8 -*-
from .com import *  # noqa

DATABASES = {
    'default': env.db('DEVDB_URL', default='sqlite:///db.sqlite3')
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])