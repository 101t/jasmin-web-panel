# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url
from django.urls import path, re_path
from .views import (
    signin_view,
    signout_view,
)

app_name = 'users'

urlpatterns = [
    #path('manage/', global_manage, name='global_manage'),
    #path('', home_view, name='home_view'),
    path(route='login/', view=signin_view, name="signin_view",),
    path(route='logout/', view=signout_view, name="signout_view",),
]