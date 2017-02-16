
from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, MTRouter
@user_passes_test(lambda u: u.is_superuser)
def mtrouter_view(request):
	args = {}
	return render(request, 'administration/mtrouter.html', args)
@user_passes_test(lambda u: u.is_superuser)
def mtrouter_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			mtrouter = MTRouter(telnet=tc.telnet)
			args = mtrouter.list()
		elif service == "add":
			tc = TelnetConnection()
			mtrouter = MTRouter(telnet=tc.telnet)
			mtrouter.create(data={
				"type": request.POST.get("type"),
				"order": request.POST.get("order"),
				"rate": request.POST.get("rate"),
				"smppconnectors": request.POST.get("smppconnectors"),
				"filters": request.POST.get("filters"),
			})
		elif service == "delete":
			tc = TelnetConnection()
			mtrouter = MTRouter(telnet=tc.telnet)
			args = mtrouter.destroy(order=request.POST.get("order"))
	return HttpResponse(json.dumps(args), content_type='application/json')