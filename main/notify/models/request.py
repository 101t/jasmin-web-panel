# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.db import models
from django.conf import settings
from django.urls import reverse, reverse_lazy

from main.core.models import TimeStampedModel
from main.users.models import User

from crequest.middleware import CrequestMiddleware
from autoslug import AutoSlugField
import os

def _handle_notification_file(instance, filename):
	name, extension = os.path.splitext(filename)
	return "notify/{}{}".format(instance.slug, ext)

class NotificationRequest(TimeStampedModel):
	class Meta:
		verbose_name = _("Notification Request")
		verbose_name_plural = _("Notification Requests")
		ordering = ("-created",)
	GENERAL = "general"
	CUSTOM = "custom"
	TYPES = (
		(GENERAL, _("General"),),
		(CUSTOM, _("Custom"),),
	)
	title = models.CharField(_("Title"), max_length=255,)
	slug  = AutoSlugField(populate_from='title', unique=True)
	body  = models.TextField(_("Description"),)
	file  = models.FileField(upload_to=_handle_notification_file, blank=True, null=True, verbose_name=_("File"))
	user  = models.ForeignKey(User, verbose_name=_("Caller"), on_delete=models.CASCADE)
	users = models.ManyToManyField(User, blank=True, verbose_name=_("To Users"), related_name='notificationrequest_users')
	staff_only = models.BooleanField(default=False, verbose_name=_("User Staff Only"))
	requesttype     = models.CharField(_("Request Type"), max_length=24, default=GENERAL, choices=TYPES)
	count  = models.PositiveIntegerField(verbose_name=_("Received user Count"), default=0)

	def __str__(self):
		return self.title
	def save(self, *args, **kwargs):
		request = CrequestMiddleware.get_request()
		if self.user is None:
			request = CrequestMiddleware.get_request()
			if request:
				if request.user.is_authenticated:
					self.user = request.user
			if self.user is None: # IF IT IS STILL NONE
				self.user = User.objects.first()
		super(NotificationRequest, self).save(*args, **kwargs)
	def get_dict(self):
		basedic = TimeStampedModel.get_dict(self).copy()
		dic = {
			"title": self.title,
			"slug": self.slug,
			"body": self.body,
			"file": {"url": self.file.url, "name": self.file.name} if self.file else {"url": "", "name": ""},
			"user": self.user.pk if self.user else -1,
			"requesttype": self.get_requesttype_display(),
			"requesttype0": self.requesttype,
		}
		basedic.update(dic)
		return basedic
	def get_absolute_url(self):
		return reverse_lazy('notify:notify_detail', kwargs=dict(requesttype=self.requesttype, slug=self.slug))