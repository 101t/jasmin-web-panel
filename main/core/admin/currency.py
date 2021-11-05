from django.utils.translation import gettext, gettext_lazy as _ # noqa
from django.contrib import admin

from ..models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("enabled", "name", "code", "order",)
    list_filter = ("enabled",)
    search_fields = ("name", "code",)
