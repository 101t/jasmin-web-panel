
from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, MORouter
@user_passes_test(lambda u: u.is_superuser)
def morouter_view(request):
	args = {}
	return render(request, 'administration/morouter.html', args)
@user_passes_test(lambda u: u.is_superuser)
def morouter_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			morouter = MORouter(telnet=tc.telnet)
			args = morouter.list()
		elif service == "add":
			tc = TelnetConnection()
			morouter = MORouter(telnet=tc.telnet)
			morouter.create(data={
				"type": request.POST.get("type"),
				"order": request.POST.get("order"),
				"smppconnectors": request.POST.get("smppconnectors"),
				"filters": request.POST.get("filters"),
			})
		elif service == "delete":
			tc = TelnetConnection()
			morouter = MORouter(telnet=tc.telnet)
			args = morouter.destroy(order=request.POST.get("order"))
	return HttpResponse(json.dumps(args), content_type='application/json')