# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext as _
from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect, render, redirect, HttpResponse
from django.db.models import Q
from django.urls import reverse
from django.conf import settings

def reset_view(request):
    return render(request, "auth/reset.html")