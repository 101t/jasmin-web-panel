# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.conf.urls import url
from django.urls import path, re_path
from .views import *

app_name = 'users'

urlpatterns = [
    path(route='profile/', view=profile_view, name='profile_view'),
    path(route='settings/', view=settings_view, name='settings_view'),
    path(route='activity_log/', view=activity_log_view, name='activity_log_view'),
    path(route='login/', view=signin_view, name="signin_view",),
    path(route='logout/', view=signout_view, name="signout_view",),
]