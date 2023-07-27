from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

import json

from main.core.smpp import HTTPCCM


@login_required
def httpccm_view(request):
    return render(request, "web/content/httpccm.html")


@login_required
def httpccm_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    httpccm = None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'delete']:
            httpccm = HTTPCCM(telnet=request.telnet)
        if httpccm:
            if s == "list":
                args = httpccm.list()
                res_status, res_message = 200, _("OK")
            elif s == "add":
                httpccm.create(data=dict(
                    cid=request.POST.get("cid"),
                    url=request.POST.get("url"),
                    method=request.POST.get("method"),
                ))
                res_status, res_message = 200, _("HTTPCCM added successfully!")
            elif s == "delete":
                args = httpccm.destroy(cid=request.POST.get("cid"))
                res_status, res_message = 200, _("HTTPCCM deleted successfully!")
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
