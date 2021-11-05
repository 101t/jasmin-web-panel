# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models

from .timestamped import TimeStampedModel

class EmailServer(TimeStampedModel):
    class Meta:
        verbose_name = _("Email Server")
        verbose_name_plural = _("Email Servers")
    ADMIN   = "admin"
    SECURITY = "security"
    INFO    = "info"
    ACCOUNTTYPES = (
        (ADMIN, _("Administration"),), 
        (SECURITY, _("Security"),), 
        (INFO, _("Information"),),
    )
    server  = models.CharField(_("Server"), max_length=50)
    port    = models.PositiveIntegerField(_("Port"))
    username = models.CharField(_("Username / Email"), max_length=50)
    password = models.CharField(_("Password"), max_length=50)
    ssl     = models.BooleanField(_("SSL Support"), default=True)
    level   = models.CharField(_("Account Type"), max_length=24, default=INFO, choices=ACCOUNTTYPES)
    active  = models.BooleanField(_("Is Active"), default=True)
    
    def __str__(self):
        return self.server

def get_available_server():
    return EmailServer.objects.filter(active=True).first()