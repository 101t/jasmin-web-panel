# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models

from autoslug import AutoSlugField
from .timestamped import TimeStampedModel
import decimal

class Currency(models.Model):
	class Meta:
		verbose_name = _("Currency")
		verbose_name_plural = _("Currencies")
		ordering = ("enabled", "order",)
	enabled = models.BooleanField(_("Is Enabled"), default=True)
	name 	= models.CharField(_("Currency Name"), max_length=64)
	slug 	= AutoSlugField(populate_from='name', unique=True)
	code 	= models.CharField(_("Currency Code"), max_length=8)
	code3   = models.CharField(_("Currency Code 3"), max_length=8, blank=True, null=True)
	symbol  = models.CharField(_("Currency Symbol"), max_length=8, blank=True, null=True)
	order	= models.PositiveIntegerField(_("Currency Order"))
	def __str__(self):
		return self.name
	def get_dict(self):
		return {
			"pk": self.pk,
			"enabled": self.enabled,
			"name": self.name,
			"slug": self.slug,
			"code": self.code,
			"order": self.order,
		}

def get_available_currencies():
	return Currency.objects.values_list('code', flat=True)