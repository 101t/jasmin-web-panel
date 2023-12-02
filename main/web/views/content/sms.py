from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

import json

from main.core.smpp import HTTPCCM


@login_required
def send_sms_view(request):
    return render(request, "web/content/send_sms.html")


@login_required
def send_sms_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    args['msisdn'] = request.POST.get("msisdn")
    args['sms'] = request.POST.get("sms")
    res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
