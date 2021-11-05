# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import gettext_lazy as _
from django.conf import settings


def site(request):
    return {
        "SETTINGS": settings,
    }
