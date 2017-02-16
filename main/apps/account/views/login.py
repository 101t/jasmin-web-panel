
from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse

def login_view(request):
	args = {}
	if request.POST:
		username = request.POST['username'].replace(' ', '').lower()
		password = request.POST['password'].strip()
		user = authenticate(username=username, password=password)
		if user is not None and user.is_active:
			login(request, user)
			return HttpResponseRedirect(request.POST.get('next') if request.POST.get('next') != "" else reverse('dashboard_view'))
		msj = "Username or Password invalid"
		messages.add_message(request, messages.WARNING, msj)
	args["next"] = request.GET.get("next", "")
	return render(request, 'account/login.html', args)

def logout_view(request):
	logout(request)
	return HttpResponseRedirect(reverse('login_view'))