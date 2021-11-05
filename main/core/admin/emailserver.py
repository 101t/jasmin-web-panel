# -*- encoding: utf-8 -*-
from django.utils.translation import gettext_lazy as _  # noqa
from django.contrib import admin

from ..models import EmailServer


@admin.register(EmailServer)
class EmailServerAdmin(admin.ModelAdmin):
    list_display = ("server", "port", "ssl", "active", "username", "level",)
    list_filter = ("level",)
    search_fields = ("server", "username",)
