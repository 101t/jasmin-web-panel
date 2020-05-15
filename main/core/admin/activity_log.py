from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib import admin, messages

from ..utils import USER_SEARCH_FIELDS
from ..models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = ("ip", "user", "service", "method", "path",)
	list_filter = ("method", "service")
	search_fields = ("ip", "path",) + USER_SEARCH_FIELDS