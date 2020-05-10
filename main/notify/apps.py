# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NotifyConfig(AppConfig):
    name = "main.notify"
    verbose_name = _("Notifications")
    def ready(self):
        import main.notify.signals