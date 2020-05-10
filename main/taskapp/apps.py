# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from django.apps import AppConfig
from django.conf import settings
from .celery import app

class CeleryConfig(AppConfig):
	name = "main.taskapp"
	verbose_name = "Celery Config"
	label = "celeryapp"

	def ready(self):
		# Using a string here means the worker will not have to
		# pickle the object when using Windows.
		app.config_from_object('django.conf:settings' , namespace='CELERY')
		app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)