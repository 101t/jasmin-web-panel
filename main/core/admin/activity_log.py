from django.contrib import admin

from ..utils import USER_SEARCH_FIELDS
from ..models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("ip", "user", "service", "method", "path",)
    list_filter = ("method", "service")
    search_fields = ("ip", "path",) + USER_SEARCH_FIELDS
