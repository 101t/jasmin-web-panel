# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.apps import AuthConfig

AuthConfig.verbose_name = _("Groups")

class UsersConfig(AppConfig):
    name = "main.users"
    verbose_name = _("Users")