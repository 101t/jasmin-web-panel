# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import ugettext_lazy as _

from django import forms
from ..models import User

class PasswordResetRequestForm(forms.Form):
	email_or_username = forms.CharField(label=_("Email or Username"), widget=forms.TextInput(attrs={'placeholder': _('Email or Username')}), max_length=254,)

class SetPasswordForm(forms.Form):
	"""
	A form that lets a user change set their password without entering the old
	password
	"""
	error_messages = {
		'password_mismatch': ("The two password fields didn't match."),
	}
	new_password1 = forms.CharField(label=_("New password"), widget=forms.PasswordInput(attrs={'placeholder': 'New password'}))
	new_password2 = forms.CharField(label=_("New password confirmation"), widget=forms.PasswordInput(attrs={'placeholder': 'New password confirmation'}))

	def clean_new_password2(self):
		password1 = self.cleaned_data.get('new_password1')
		password2 = self.cleaned_data.get('new_password2')
		if password1 and password2:
			if password1 != password2:
				raise forms.ValidationError(
					self.error_messages['password_mismatch'],
					code='password_mismatch',
					)
		return password2