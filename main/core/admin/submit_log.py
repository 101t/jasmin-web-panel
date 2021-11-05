# -*- encoding: utf-8 -*-
from django.utils.translation import gettext_lazy as _  # noqa
from django.contrib import admin

from ..models import SubmitLog


@admin.register(SubmitLog)
class SubmitLogAdmin(admin.ModelAdmin):

    list_display = ("msgid", "source_connector", "routed_cid", "source_addr", "destination_addr", "rate", "pdu_count",
                    "status", "uid", "trials", "created_at", "status_at",)
    list_filter = ("status",)
    search_fields = ("source_connector", "source_addr", "destination_addr",)
    date_hierarchy = "created_at"
