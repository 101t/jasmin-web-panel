# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone as djtz
from django.conf import settings

from main.notify.models import Notification, NotificationRequest
from main.users.models import User
from main.core.utils import get_query, paginate

import json

PER_PAGE = 25

@login_required
def notify_list(request):
	collectionlist = Notification.objects.filter(user=request.user).order_by("-created")
	q = request.GET.get("q")
	if q:
		entry_query = get_query(q, ("title", "body",))
		collectionlist = collectionlist.filter(entry_query)
	collectionlist = paginate(collectionlist, per_page=PER_PAGE, page=request.GET.get("page", 1))
	template_name = 'web/notify-list.html'
	return render(request, template_name, dict(collectionlist=collectionlist))

@login_required
def notify_detail(request, requesttype="", slug=""):
	obj = get_object_or_404(NotificationRequest, slug=slug, requesttype=requesttype)
	template_name = 'web/notify-detail.html'
	return render(request, template_name, dict(obj=obj))

@login_required
def notify_manage(request):
	args, resstatus, resmessage = {}, 400, _("Sorry, Command does not matched.")
	if request.GET and request.is_ajax():
		s = request.GET.get("s")
		if s == "all":
			collectionlist = Notification.objects.filter(user=request.user, read=False).order_by("-created")[:10]
			args = list(map(lambda a: a.get_small_dict(), collectionlist))
		elif s == "markall":
			Notification.objects.filter(user=request.user).update(read=True)
			resmessage = _("All Notifications are marked as read")
			resstatus = 200
		elif s == "mark":
			Notification.objects.filter(user=request.user).filter(pk__in=request.GET.getlist("pk")).update(read=True)
			obj = Notification.objects.filter(pk__in=request.GET.getlist("pk")).first()
			if obj:
				args["href"] = obj.href
			resmessage = _("This Notification marked as read")
			resstatus = 200
		elif s == "unmark":
			Notification.objects.filter(user=request.user).filter(pk__in=request.GET.getlist("pk")).update(read=False)
			obj = Notification.objects.filter(pk__in=request.GET.getlist("pk")).first()
			if obj:
				args["href"] = obj.href
			resmessage = _("This Notification marked as unread")
			resstatus = 200
	if isinstance(args, dict):
		args["status"] = resstatus
		args["message"] = str(resmessage)
	else:
		resstatus = 200
	return HttpResponse(json.dumps(args), status=resstatus, content_type="application/json")
