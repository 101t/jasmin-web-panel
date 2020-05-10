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

from main.core.smpp import TelnetConnection, MTRouter

@login_required
def mtrouter_view(request):
    return render(request, "web/content/mtrouter.html")

@login_required
def mtrouter_view_manage(request):
    args, resstatus, resmessage = {}, 400, _("Sorry, Command does not matched.")
    tc, mtrouter = None, None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'delete']:
            tc = TelnetConnection()
            mtrouter = MTRouter(telnet=tc.telnet)
        if tc and mtrouter:
            if s == "list":
                args = mtrouter.list()
                resstatus, resmessage = 200, _("OK")
            elif s == "add":
                try:
                    mtrouter.create(data=dict(
                        type=request.POST.get("type"),
                        order=request.POST.get("order"),
                        rate=request.POST.get("rate"),
                        smppconnectors=request.POST.get("smppconnectors"),
                        #httpconnectors=request.POST.get("httpconnectors"),
                        filters=request.POST.get("filters"),
                    ))
                    resstatus, resmessage = 200, _("MT Router added successfully!")
                except Exception as e:
                    resmessage = e
            elif s == "delete":
                args = mtrouter.destroy(order=request.POST.get("order"))
                resstatus, resmessage = 200, _("MT Router deleted successfully!")
    if isinstance(args, dict):
        args["status"] = resstatus
        args["message"] = str(resmessage)
    else:
        resstatus = 200
    return HttpResponse(json.dumps(args), status=resstatus, content_type="application/json")