# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from main.users.models import User

from ..forms import NotificationRequestForm
from ..models import NotificationRequest

@admin.register(NotificationRequest)
class NotificationRequestAdmin(admin.ModelAdmin):
	form = NotificationRequestForm
	list_display = ("title", "user", "created",)
	search_fields = ("title", "user__username", "user__first_name", "user__last_name", "user__email",)
	def render_change_form(self, request, context, *args, **kwargs):
		context['adminform'].form.fields['user'].queryset = User.objects.exclude(is_staff=False, is_superuser=False)
		context['adminform'].form.fields['users'].queryset = User.objects.filter(is_staff=True, is_superuser=True)
		return super(NotificationRequestAdmin, self).render_change_form(request, context, *args, **kwargs)