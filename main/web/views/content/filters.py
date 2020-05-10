# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone as djtz
from django.conf import settings

import json

from main.core.smpp import TelnetConnection, Filters

@login_required
def filters_view(request):
    return render(request, "web/content/filters.html")

@login_required
def filters_view_manage(request):
    args, resstatus, resmessage = {}, 400, _("Sorry, Command does not matched.")
    tc, filters = None, None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'delete']:
            tc = TelnetConnection()
            filters = Filters(telnet=tc.telnet)
        if tc and filters:
            if s == "list":
                args = filters.list()
            elif s == "add":
                filters.create(data=dict(
                    fid=request.POST.get("fid"),
                    type=request.POST.get("type"),
                    parameter=request.POST.get("parameter"),
                ))
            elif s == "delete":
                args = filters.destroy(fid=request.POST.get("fid"))
    if isinstance(args, dict):
        args["status"] = resstatus
        args["message"] = str(resmessage)
    else:
        resstatus = 200
    return HttpResponse(json.dumps(args), status=resstatus, content_type="application/json")