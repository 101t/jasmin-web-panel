# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.utils.timezone import now
from django.utils import timezone
from django.db.models import Q

from main.users.models import User
from main.taskapp.celery import DEFAULT_RETRY_DELAY, MAX_RETRIES, revoke_task
from celery.decorators import task
from celery.utils.log import get_task_logger

import json

logger = get_task_logger(__name__)

@task(default_retry_delay=DEFAULT_RETRY_DELAY, max_retries=MAX_RETRIES)
def send_notification(userid, title, body, href):
	from main.notify.models import Notification
	from main.notify.livecast import send_to_session
	try:
		user = User.objects.get(pk=userid)
		data = dict(
			user=user,
			title=title,
			body=body,
		)
		if href:
			data["href"] = href
		Notification.objects.create(**data)
		send_to_session(caller=None, callee=user)
	except User.DoesNotExist:
		pass
'''
Usage:

from main.notify.tasks import send_notification
send_notification.apply_async(kwargs=dict(userid=1, title="Test", body="description", href=None), countdown=1,)

'''

@task(default_retry_delay=DEFAULT_RETRY_DELAY, max_retries=MAX_RETRIES)
def request_notification_task(request_notification_pk):
	from main.notify.models import NotificationRequest, Notification
	from main.notify.livecast import send_to_session
	try:
		request_notification = NotificationRequest.objects.get(pk=request_notification_pk)
	except NotificationRequest.DoesNotExist:
		return
	staff_only = request_notification.staff_only
	users = User.objects.none()
	title = request_notification.title or str(_("New Notification"))
	notifybody = request_notification.body
	# if request_notification.requesttype == NotificationRequest.GENERAL or request_notification.requesttype == NotificationRequest.CUSTOM:
	# 	title = str(_("New %(requesttype)s Notification") % dict(requesttype=request_notification.get_requesttype_display()))
	if staff_only:
		users = User.objects.filter(is_staff=True, is_active=True)
	else:
		users = User.objects.filter(is_active=True)
	users = users.distinct()
	request_notification.count = users.count()
	request_notification.save()
	for user in users:
		data = dict(
			title=title,
			body=notifybody,
			href=request_notification.get_absolute_url(),
			user=user,
		)
		Notification.objects.create(**data)
		send_to_session(caller=None, callee=user)