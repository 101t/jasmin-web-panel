# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone as djtz
from django.conf import settings

import json

from main.core.smpp import TelnetConnection, MORouter


@login_required
def morouter_view(request):
    return render(request, "web/content/morouter.html")


@login_required
def morouter_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    tc, morouter = None, None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'delete']:
            tc = TelnetConnection()
            morouter = MORouter(telnet=tc.telnet)
        if tc and morouter:
            if s == "list":
                args = morouter.list()
                res_status, res_message = 200, _("OK")
            elif s == "add":
                try:
                    morouter.create(data=dict(
                        type=request.POST.get("type"),
                        order=request.POST.get("order"),
                        smppconnectors=request.POST.get("smppconnectors"),
                        httpconnectors=request.POST.get("httpconnectors"),
                        filters=request.POST.get("filters"),
                    ))
                    res_status, res_message = 200, _("MO Router added successfully!")
                except Exception as e:
                    res_message = e
            elif s == "delete":
                args = morouter.destroy(order=request.POST.get("order"))
                res_status, res_message = 200, _("MO Router deleted successfully!")
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
