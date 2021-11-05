# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Count, Q
from django.conf import settings

from .timestamped import TimeStampedModel
from ..utils import is_json

import json

class ActivityLog(TimeStampedModel):
    class Meta:
        verbose_name = _("Activity Log")
        verbose_name_plural = _("Activity Logs")
        ordering = ("-created",)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL)
    service    = models.CharField(verbose_name=_("Log Name"), max_length=100)
    method     = models.CharField(verbose_name=_("Request Method"), max_length=10)
    params     = models.TextField(verbose_name=_("Request Parameters"), default="{}")
    path       = models.CharField(verbose_name=_("Log Path"), max_length=140)
    ip         = models.GenericIPAddressField(verbose_name=_("IP Address"))
    user_agent = models.TextField(verbose_name=_("User Agent"), default="{}")

    def __str__(self):
        return self.user.get_full_name() if self.user else str(_("Guest User"))
    def get_dict(self):
        return dict(
            user=self.user.pk,
            service=self.service,
            method=self.method,
            params=json.loads(self.params) if is_json(self.params) else {},
            path=self.path,
            ip=self.ip,
            user_agent=json.loads(self.user_agent) if is_json(self.user_agent) else {},
        )
    def get_json(self):
        return json.dumps(self.get_dict())