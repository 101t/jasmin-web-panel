# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

import json

from main.core.smpp import TelnetConnection, Filters


@login_required
def filters_view(request):
    return render(request, "web/content/filters.html")


@login_required
def filters_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    filters = None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'delete']:
            filters = Filters(telnet=request.telnet)
        if filters:
            if s == "list":
                args = filters.list()
                res_status, res_message = 200, _("OK")
            elif s == "add":
                try:
                    filters.create(data=dict(
                        fid=request.POST.get("fid"),
                        type=request.POST.get("type"),
                        parameter=request.POST.get("parameter"),
                    ))
                    res_status, res_message = 200, _("Filter added successfully!")
                except Exception as e:
                    res_message = str(e)
            elif s == "delete":
                args = filters.destroy(fid=request.POST.get("fid"))
                res_status, res_message = 200, _("Filter deleted successfully!")
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
