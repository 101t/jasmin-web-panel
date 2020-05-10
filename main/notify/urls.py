# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.urls import path,include
from django.conf.urls import url

from main.notify.views import *

app_name = 'notify'

urlpatterns = [
    path('manage/', notify_manage, name='notify_manage'),
    path('<str:requesttype>/<str:slug>/', notify_detail, name='notify_detail'),
    path('', notify_list, name='notify_list'),
]
