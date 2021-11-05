# -*- encoding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from main.core.smpp import TelnetConnection, Users


@login_required
def users_view(request):
    return render(request, "web/content/users.html")


@login_required
def users_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    users = None
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
        if s in ['list', 'add', 'edit', 'delete', 'enable', 'disable', 'smpp_unbind', 'smpp_ban']:
            users = Users(telnet=request.telnet)
        if users:
            if s == "list":
                args = users.list()
                res_status, res_message = 200, _("OK")
            elif s == "add":
                try:
                    users.create(data=dict(
                        uid=request.POST.get("uid"),
                        gid=request.POST.get("gid"),
                        username=request.POST.get("username"),
                        password=request.POST.get("password"),
                    ))
                    res_status, res_message = 200, _("User added successfully!")
                except Exception as e:
                    res_message = e
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
                    res_status, res_message = 200, _("User edited successfully!")
                except Exception as e:
                    res_message = e
            elif s == "delete":
                args = users.destroy(uid=request.POST.get("uid"))
                res_status, res_message = 200, _("User deleted successfully!")
            elif s == "enable":
                args = users.enable(uid=request.POST.get("uid"))
                res_status, res_message = 200, _("User enabled successfully!")
            elif s == "disable":
                args = users.disable(uid=request.POST.get("uid"))
                res_status, res_message = 200, _("User disabled successfully!")
            elif s == "smpp_unbind":
                args = users.smpp_unbind(uid=request.POST.get("uid"))
                res_status, res_message = 200, _("User SMPP Unbind successfully!")
            elif s == "smpp_ban":
                args = users.smpp_ban(uid=request.POST.get("uid"))
                res_status, res_message = 200, _("User SMPP Ban successfully!")
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
