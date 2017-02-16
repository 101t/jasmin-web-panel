
from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, Groups
@user_passes_test(lambda u: u.is_superuser)
def groups_view(request):
	args = {}
	return render(request, 'administration/groups.html', args)
@user_passes_test(lambda u: u.is_superuser)
def groups_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			groups = Groups(telnet=tc.telnet)
			args = groups.list()
		elif service == "add":
			tc = TelnetConnection()
			groups = Groups(telnet=tc.telnet)
			groups.create(data={
				"gid": request.POST.get("gid"),
			})
		elif service == "delete":
			tc = TelnetConnection()
			groups = Groups(telnet=tc.telnet)
			args = groups.destroy(gid=request.POST.get("gid"))
		elif service == "enable":
			tc = TelnetConnection()
			groups = Groups(telnet=tc.telnet)
			args = groups.enable(gid=request.POST.get("gid"))
		elif service == "disable":
			tc = TelnetConnection()
			groups = Groups(telnet=tc.telnet)
			args = groups.disable(gid=request.POST.get("gid"))
	return HttpResponse(json.dumps(args), content_type='application/json')