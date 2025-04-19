from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from main.core.utils import get_client_ip, is_online
from main.core.tools import require_get_ajax


@login_required
def dashboard_view(request):
    ip_address = get_client_ip(request)
    return render(request, "web/dashboard.html", dict(ip_address=ip_address))


@require_get_ajax
def global_manage(request):
    response = {}
    s = request.GET.get("s")
    if s == "gw_state":
        # CHECK GATEWAY BINDING OK
        response["status"], response["message"] = is_online(
            host=settings.TELNET_HOST, port=settings.TELNET_PORT)
    return JsonResponse(response, status=200)
