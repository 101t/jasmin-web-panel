# -*- encoding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxLengthValidator, MinLengthValidator, EmailValidator, RegexValidator
from django import forms

class SignInForm(forms.Form):
    default_attrs = {'class': 'form-control'}
    username_validators = [
        MaxLengthValidator(limit_value=255, message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)), 
        MinLengthValidator(limit_value=2, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=2)),
    ]
    password_validators = [
        MaxLengthValidator(limit_value=255, message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)), 
        # PATCH: limit_value = 1, min_length = 5
        MinLengthValidator(limit_value=1, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=5)),
    ]
    username = forms.CharField(widget=forms.TextInput(
        attrs=default_attrs.update(dict(placeholder=_("Email or Username")))
    ), validators=username_validators, required=True, label=_("Email or Username"))
    password  = forms.CharField(widget=forms.PasswordInput(
        attrs=default_attrs.update(dict(placeholder=_("Password")))
    ), validators=password_validators, required=True, label=_("Password"))