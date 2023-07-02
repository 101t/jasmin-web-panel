from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django import forms

from main.users.models import User


class ChangePhotoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('img',)


class ChangePasswordForm(forms.Form):
    default_attrs = {'class': 'form-control'}
    password0_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=1, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=5)),
    ]
    password_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=5, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=5)),
    ]
    password = forms.CharField(widget=forms.PasswordInput(
        attrs=default_attrs.update(dict(placeholder=_("Current Password")))
    ), validators=password0_validators, required=True, label=_("Password"))
    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs=default_attrs.update(dict(placeholder=_("New Password")))
    ), validators=password_validators, required=True, label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs=default_attrs.update(dict(placeholder=_("New Password Confirmation")))
    ), validators=password_validators, required=True, label=_("Password Confirmation"))

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if not password1 or not password2 or not password1 == password2:
            self.add_error(field="password2", error=_("The two password fields did not matched."))


class ProfileForm(forms.Form):
    first_name_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=2, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=2)),
    ]
    last_name_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=2, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=2)),
    ]
    email_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=10, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=10)),
    ]
    url_validators = [
        MaxLengthValidator(limit_value=255,
                           message=_("Maximum length allowed is %(max_length)s") % dict(max_length=255)),
        MinLengthValidator(limit_value=10, message=_("Minimum length allowed is %(min_length)s") % dict(min_length=10)),
    ]
    first_name = forms.CharField(widget=forms.TextInput(), validators=first_name_validators, required=True,
                                 label=_("First Name"))
    last_name = forms.CharField(widget=forms.TextInput(), validators=last_name_validators, required=True,
                                label=_("Last Name"))
    email = forms.EmailField(widget=forms.EmailInput(), validators=email_validators, required=True, label=_("Email"))
