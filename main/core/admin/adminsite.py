# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.conf import settings

AdminSite.site_title = settings.SITE_TITLE
AdminSite.site_header = settings.SITE_HEADER
AdminSite.index_title = settings.INDEX_TITLE