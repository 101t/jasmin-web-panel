
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
	args = {}
	return render(request, 'account/dashboard.html', args)
