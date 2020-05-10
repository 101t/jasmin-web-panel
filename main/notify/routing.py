# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.urls import include, path

from main.notify.consumers import *

websocket_urlpatterns = [
    path('ws/session/<slug:session_id>/', SessionConsumer, name="session"),
    path('ws/broadcast/', BroadcastConsumer, name="broadcast"),
]