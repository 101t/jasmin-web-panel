
from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, Filters
def filters_view(request):
	args = {}
	return render(request, 'administration/filters.html', args)
def filters_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			filters = Filters(telnet=tc.telnet)
			args = filters.list()
		elif service == "add":
			tc = TelnetConnection()
			filters = Filters(telnet=tc.telnet)
			filters.create(data={
				"fid": request.POST.get("fid"),
				"type": request.POST.get("type"),
				"parameter": request.POST.get("parameter"),
			})
		elif service == "delete":
			tc = TelnetConnection()
			filters = Filters(telnet=tc.telnet)
			args = filters.destroy(fid=request.POST.get("fid"))
	return HttpResponse(json.dumps(args), content_type='application/json')