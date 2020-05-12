# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone as djtz
from django.conf import settings

from main.core.utils import get_client_ip

@login_required
def dashboard_view(request):
    ip_address = get_client_ip(request)
    return render(request, "web/dashboard.html", dict(ip_address=ip_address))

def welcome_view(request):
    import django, sys
    python_version = "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    return render(request, "web/welcome.html", dict(
        django_version=django.get_version(),
        python_version=python_version,
        platform=sys.platform,
        ))

def global_manage(request):
    args, resstatus, resmessage = {}, 400, _("Sorry, Command does not matched.")
    if request.GET and request.is_ajax():
        s = request.GET.get("s")
    if isinstance(args, dict):
        args["status"] = resstatus
        args["message"] = str(resmessage)
    else:
        resstatus = 200
    return HttpResponse(json.dumps(args), status=resstatus, content_type="application/json")