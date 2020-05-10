# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from ..models import Tokenizer

@admin.register(Tokenizer)
class TokenizerAdmin(admin.ModelAdmin):
	list_display = ("guid", "uidb64", "token",)
	search_fields = ("guid",)