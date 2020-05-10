# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import ugettext as _
from django import forms

from main.users.models import User
from ..models import NotificationRequest

class NotificationRequestForm(forms.ModelForm):
	class Meta:
		model = NotificationRequest
		exclude = ()
	selectall = forms.BooleanField(required=False, label=_("Select all users"), help_text=_("Send this notification to all users in system."))
	def save(self, *args, **kwargs):
		if self.cleaned_data["selectall"]:
			pass
			# if all users selected will modify form user field to all users ids
			# users = User.objects.values_list("pk", flat=True)
			# if users:
			# 	self.data.setlist("users", users)
		return super(NotificationRequestForm, self).save(*args, **kwargs)
	def clean(self):
		if self.cleaned_data["selectall"]:
			# if all users selected will modify form user field to all users ids
			self.cleaned_data["users"] = User.objects.filter(is_active=True).filter(is_verified=True).values_list("pk", flat=True)
		return self.cleaned_data