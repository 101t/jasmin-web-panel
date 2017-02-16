
from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, Users
from ..managers.usermanager import UserManager

def users_view(request):
	args = {}
	return render(request, 'administration/users.html', args)
def users_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			args = users.list()
		elif service == "add":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			users.create(data={
				"uid": request.POST.get("uid"),
				"gid": request.POST.get("gid"),
				"username": request.POST.get("username"),
				"password": request.POST.get("password"),
			})
			u = UserManager().add(data={
				"uid": request.POST.get("uid"),
				"gid": request.POST.get("gid"),
				"username": request.POST.get("username"),
				"password": request.POST.get("password"),
			})
		elif service == "edit":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			data=[
				["uid", request.POST.get("uid")],
				["gid", request.POST.get("gid")],
				["username", request.POST.get("username")],
				["mt_messaging_cred", "valuefilter", "priority", request.POST.get("priority_f", "^[0-3]$")],
				["mt_messaging_cred", "valuefilter", "content", request.POST.get("content_f", ".*")],
				["mt_messaging_cred", "valuefilter", "src_addr", request.POST.get("src_addr_f", ".*")],
				["mt_messaging_cred", "valuefilter", "dst_addr", request.POST.get("dst_addr_f", ".*")],
				["mt_messaging_cred", "valuefilter", "validity_period", request.POST.get("validity_period_f", "^\\d+$")],
				["mt_messaging_cred", "defaultvalue", "src_addr", request.POST.get("src_addr_d", "None")],
				["mt_messaging_cred", "quota", "http_throughput", request.POST.get("http_throughput", "ND")],
				["mt_messaging_cred", "quota", "balance", request.POST.get("balance", "ND")],
				["mt_messaging_cred", "quota", "smpps_throughput", request.POST.get("smpps_throughput", "ND")],
				["mt_messaging_cred", "quota", "early_percent", request.POST.get("early_percent", "ND")],
				["mt_messaging_cred", "quota", "sms_count", request.POST.get("sms_count", "ND")],
				["mt_messaging_cred", "authorization", "dlr_level", "True" if request.POST.get("dlr_level", True) else "False"],
				["mt_messaging_cred", "authorization", "http_long_content", "True" if request.POST.get("http_long_content", True) else "False"],
				["mt_messaging_cred", "authorization", "http_send", "True" if request.POST.get("http_send", True) else "False"],
				["mt_messaging_cred", "authorization", "http_dlr_method", "True" if request.POST.get("http_dlr_method", True) else "False"],
				["mt_messaging_cred", "authorization", "validity_period", "True" if request.POST.get("validity_period", True) else "False"],
				["mt_messaging_cred", "authorization", "priority", "True" if request.POST.get("priority", True) else "False"],
				["mt_messaging_cred", "authorization", "http_bulk", "True" if request.POST.get("http_bulk", False) else "False"],
				["mt_messaging_cred", "authorization", "src_addr", "True" if request.POST.get("src_addr", True) else "False"],
				["mt_messaging_cred", "authorization", "http_rate", "True" if request.POST.get("http_rate", True) else "False"],
				["mt_messaging_cred", "authorization", "http_balance", "True" if request.POST.get("http_balance", True) else "False"],
				["mt_messaging_cred", "authorization", "smpps_send", "True" if request.POST.get("smpps_send", True) else "False"],
			]
			if len(request.POST.get("password")) > 0:
				data.append(["password", request.POST.get("password")])
			users.partial_update(data, uid=request.POST.get("uid"))
			u = UserManager().update(data={
				"uid": request.POST.get("uid"),
				"gid": request.POST.get("gid"),
				"username": request.POST.get("username"),
				"password": request.POST.get("password"),
			}, uid=request.POST.get("uid"))
		elif service == "delete":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			args = users.destroy(uid=request.POST.get("uid"))
			u = UserManager().delete(uid=request.POST.get("uid"))
		elif service == "enable":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			args = users.enable(uid=request.POST.get("uid"))
		elif service == "disable":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			args = users.disable(uid=request.POST.get("uid"))
		elif service == "smpp_unbind":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			args = users.smpp_unbind(uid=request.POST.get("uid"))
		elif service == "smpp_ban":
			tc = TelnetConnection()
			users = Users(telnet=tc.telnet)
			args = users.smpp_ban(uid=request.POST.get("uid"))
	return HttpResponse(json.dumps(args), content_type='application/json')