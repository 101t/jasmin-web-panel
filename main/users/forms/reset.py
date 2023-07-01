from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django import forms


class ResetPasswordForm(forms.Form):
    default_attrs = {'class': 'form-control'}
    username_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=2, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=2)),
    ]
    username = forms.CharField(widget=forms.TextInput(
        attrs=default_attrs.update(dict(placeholder=_("Email or Username")))
    ), validators=username_validators, required=True, label=_("Email or Username"))


class ResetPasswordConfirmForm(forms.Form):
    default_attrs = {'class': 'form-control'}
    password_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=5, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=5)),
    ]
    password = forms.CharField(widget=forms.PasswordInput(
        attrs=default_attrs.update(dict(placeholder=_("New Password")))
    ), validators=password_validators, required=True, label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs=default_attrs.update(dict(placeholder=_("New Password Confirmation")))
    ), validators=password_validators, required=True, label=_("Password Confirmation"))

    def clean(self):
        cleaned_data = super(ResetPasswordConfirmForm, self).clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if not password or not password2 or not password == password2:
            self.add_error(field="password2", error=_("The two password fields did not matched."))
        return password
