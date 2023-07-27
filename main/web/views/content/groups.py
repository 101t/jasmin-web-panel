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

from main.core.smpp import Groups


@login_required
def groups_view(request):
    return render(request, "web/content/groups.html")


@login_required
def groups_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    groups = None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'delete', 'enable', 'disable']:
            groups = Groups(telnet=request.telnet)
        if groups:
            if s == "list":
                args = groups.list()
                res_status, res_message = 200, _("OK")
            elif s == "add":
                groups.create(data=dict(
                    gid=request.POST.get("gid"),
                ))
                res_status, res_message = 200, _("Group added successfully!")
            elif s == "delete":
                args = groups.destroy(gid=request.POST.get("gid"))
                res_status, res_message = 200, _("Group deleted successfully!")
            elif s == "enable":
                args = groups.enable(gid=request.POST.get("gid"))
                res_status, res_message = 200, _("Group enabled successfully!")
            elif s == "disable":
                args = groups.disable(gid=request.POST.get("gid"))
                res_status, res_message = 200, _("Group disabled successfully!")
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
