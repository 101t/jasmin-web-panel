from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.smpp import Users
from main.core.tools import require_post_ajax


@login_required
def users_view(request):
    return render(request, "web/content/users.html")


@require_post_ajax
def users_view_manage(request):
    response = {}
    s = request.POST.get("s")
    users = Users()
    if s == "list":
        response = users.list()
    elif s == "add":
        try:
            users.create(data=dict(
                uid=request.POST.get("uid"),
                gid=request.POST.get("gid"),
                username=request.POST.get("username"),
                password=request.POST.get("password"),
            ))
            response["message"] = str(_("User added successfully!"))
        except Exception as e:
            return JsonResponse({"message": str(e), "status": 400}, status=400)
    elif s == "edit":
        try:
            data = [
                ["uid", request.POST.get("uid")],
                ["gid", request.POST.get("gid")],
                ["username", request.POST.get("username")],
                ["mt_messaging_cred", "valuefilter", "priority", request.POST.get("priority_f", "^[0-3]$")],
                ["mt_messaging_cred", "valuefilter", "content", request.POST.get("content_f", ".*")],
                ["mt_messaging_cred", "valuefilter", "src_addr", request.POST.get("src_addr_f", ".*")],
                ["mt_messaging_cred", "valuefilter", "dst_addr", request.POST.get("dst_addr_f", ".*")],
                ["mt_messaging_cred", "valuefilter", "validity_period",
                    request.POST.get("validity_period_f", "^\\d+$")],
                ["mt_messaging_cred", "defaultvalue", "src_addr", request.POST.get("src_addr_d", "None")],
                ["mt_messaging_cred", "quota", "http_throughput", request.POST.get("http_throughput", "ND")],
                ["mt_messaging_cred", "quota", "balance", request.POST.get("balance", "ND")],
                ["mt_messaging_cred", "quota", "smpps_throughput", request.POST.get("smpps_throughput", "ND")],
                ["mt_messaging_cred", "quota", "early_percent", request.POST.get("early_percent", "ND")],
                ["mt_messaging_cred", "quota", "sms_count", request.POST.get("sms_count", "ND")],
                ["mt_messaging_cred", "authorization", "dlr_level",
                    "True" if request.POST.get("dlr_level", True) else "False"],
                ["mt_messaging_cred", "authorization", "http_long_content",
                    "True" if request.POST.get("http_long_content", True) else "False"],
                ["mt_messaging_cred", "authorization", "http_send",
                    "True" if request.POST.get("http_send", True) else "False"],
                ["mt_messaging_cred", "authorization", "http_dlr_method",
                    "True" if request.POST.get("http_dlr_method", True) else "False"],
                ["mt_messaging_cred", "authorization", "validity_period",
                    "True" if request.POST.get("validity_period", True) else "False"],
                ["mt_messaging_cred", "authorization", "priority",
                    "True" if request.POST.get("priority", True) else "False"],
                ["mt_messaging_cred", "authorization", "http_bulk",
                    "True" if request.POST.get("http_bulk", False) else "False"],
                ["mt_messaging_cred", "authorization", "src_addr",
                    "True" if request.POST.get("src_addr", True) else "False"],
                ["mt_messaging_cred", "authorization", "http_rate",
                    "True" if request.POST.get("http_rate", True) else "False"],
                ["mt_messaging_cred", "authorization", "http_balance",
                    "True" if request.POST.get("http_balance", True) else "False"],
                ["mt_messaging_cred", "authorization", "smpps_send",
                    "True" if request.POST.get("smpps_send", True) else "False"],
            ]
            password = request.POST.get("password", "")
            if len(password) > 0:
                data.append(["password", password])
            users.partial_update(data, uid=request.POST.get("uid"))
            response["message"] = str(_("User edited successfully!"))
        except Exception as e:
            return JsonResponse({"message": str(e), "status": 400}, status=400)
    elif s == "delete":
        response = users.destroy(uid=request.POST.get("uid"))
        response["message"] = str(_("User deleted successfully!"))
    elif s == "enable":
        response = users.enable(uid=request.POST.get("uid"))
        response["message"] = str(_("User enabled successfully!"))
    elif s == "disable":
        response = users.disable(uid=request.POST.get("uid"))
        response["message"] = str(_("User disabled successfully!"))
    elif s == "smpp_unbind":
        response = users.smpp_unbind(uid=request.POST.get("uid"))
        response["message"] = str(_("User SMPP Unbind successfully!"))
    elif s == "smpp_ban":
        response = users.smpp_ban(uid=request.POST.get("uid"))
        response["message"] = str(_("User SMPP Ban successfully!"))
    else:
        return JsonResponse({"message": str(_("Sorry, Command does not matched.")), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
