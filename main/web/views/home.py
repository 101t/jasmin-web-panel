# -*- encoding: utf-8 -*-
import json
import traceback
from subprocess import getoutput

from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from main.core.utils import get_client_ip

import logging
logger = logging.getLogger(__name__)


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
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    if request.GET and request.is_ajax():
        s = request.GET.get("s")
        if s == "systemctl_services_state" and settings.SYSCTL_HEALTH_CHECK:
            service_states = dict()
            for service in settings.SYSCTL_HEALTH_CHECK_SERVICES:
                try:
                    status = getoutput(f"systemctl show {service} -p SubState").split("=")[1].lower()
                    if status != "running":
                        # TODO send email or notification
                        pass
                    service_states[service] = status
                except Exception as e:
                    logger.info(f"Error occurred: {e}")
            args["service_states"] = service_states
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
