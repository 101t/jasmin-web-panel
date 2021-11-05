# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils import timezone
from django.utils.timesince import timesince

class TimeStampedModel(models.Model):
	"""
	Abstract base class that provides self-updating 'created' and 'modified' fields.
	"""
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True
	def get_dict(self):
		from main.core.utils import readabledateformat
		return {
			"created": timezone.localtime(self.created).isoformat() if self.created else None,
			"createdf": readabledateformat(timezone.localtime(self.created)) if self.created else None,
			"createds": timesince(self.created) if self.created else None,
			"modified": timezone.localtime( self.modified).isoformat() if self.modified else None,
			"modifiedf": readabledateformat(timezone.localtime(self.modified)) if self.modified else None,
			"modifieds": timesince(self.modified) if self.modified else None,
			"isedited": self.isedited,
		}
	@property
	def isedited(self):
		return False if self.created.strftime('%Y-%m-%d %H:%M:%S') == self.modified.strftime('%Y-%m-%d %H:%M:%S') else True
