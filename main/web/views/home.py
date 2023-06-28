import traceback
import logging
import pexpect
from subprocess import getoutput

from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from main.core.utils import get_client_ip, is_online

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    ip_address = get_client_ip(request)
    return render(request, "web/dashboard.html", dict(ip_address=ip_address))


def global_manage(request):
    ctx, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    if request.GET and request.is_ajax():
        s = request.GET.get("s")
        if s == "systemctl_services_state" and settings.SYSCTL_HEALTH_CHECK:
            # THIS ONLY WORKS WITH SYSTEMCTL
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
            ctx["service_states"] = service_states
        if s == "gw_state":
            # CHECK GATEWAY BINDING OK
            res_status, res_message = is_online(host=settings.TELNET_HOST, port=settings.TELNET_PORT)
    if isinstance(ctx, dict):
        ctx["status"] = res_status
        ctx["message"] = res_message
    return JsonResponse(ctx, status=200)
