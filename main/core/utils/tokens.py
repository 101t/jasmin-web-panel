# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

class EmailActiveTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) +
            str(user.email) + str(user.pin) + 
            str(user.last_name) + str(user.first_name)
        )

email_active_token = EmailActiveTokenGenerator()


class RestPassswordTokenGenertorclass(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) +
            str(user.email) + str(user.pin) + 
            str(user.last_name) + str(settings.SECRET_KEY) + str(timestamp)
        )

reset_password_token = RestPassswordTokenGenertorclass()
