from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, HTTPCCM

@user_passes_test(lambda u: u.is_superuser)
def httpccm_view(request):
	args = {}
	return render(request, 'administration/httpccm.html', args)

@user_passes_test(lambda u: u.is_superuser)
def httpccm_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			httpccm = HTTPCCM(telnet=tc.telnet)
			args = httpccm.list()
		elif service == "add":
			tc = TelnetConnection()
			httpccm = HTTPCCM(telnet=tc.telnet)
			httpccm.create(data={
				"cid": request.POST.get("cid"),
				"url": request.POST.get("url"),
				"method": request.POST.get("method"),
			})
		elif service == "delete":
			tc = TelnetConnection()
			httpccm = HTTPCCM(telnet=tc.telnet)
			args = httpccm.destroy(cid=request.POST.get("cid"))
	return HttpResponse(json.dumps(args), content_type='application/json')