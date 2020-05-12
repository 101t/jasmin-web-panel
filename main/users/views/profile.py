# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect, render, redirect, HttpResponse
from django.db.models import Q
from django.urls import reverse
from django.conf import settings

@login_required
def profile_view(request):
    return render(request, "auth/profile.html")

@login_required
def settings_view(request):
    return render(request, "auth/settings.html")

@login_required
def activity_log_view(request):
    return render(request, "auth/settings.html")