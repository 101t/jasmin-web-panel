# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    """
    Abstract base class that provides self-updating 'created' and 'modified'
    fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
filter_types = (('TransparentFilter', 'TransparentFilter',),
	('ConnectorFilter', 'ConnectorFilter',),
	('UserFilter', 'UserFilter',),
	('GroupFilter', 'GroupFilter',),
	('SourceAddrFilter', 'SourceAddrFilter',),
	('DestinationAddrFilter', 'DestinationAddrFilter',),
	('ShortMessageFilter', 'ShortMessageFilter',),
	('DateIntervalFilter', 'DateIntervalFilter',),
	('TimeIntervalFilter', 'TimeIntervalFilter',),
	('TagFilter', 'TagFilter',),
	('EvalPyFilter', 'EvalPyFilter',),
)
class FiltersModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_filters"
		verbose_name='Filters'
		verbose_name_plural = verbose_name
	type = models.CharField(u'Type', choices=filter_types, max_length=24)
	fid = models.CharField(u'Filter ID', max_length=24, unique=True)
	parameters = models.TextField(u'Parameters')
	def __str__(self):
		return self.fid

class GroupsModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_groups"
		verbose_name='Groups'
		verbose_name_plural = verbose_name
	gid = models.CharField(u'Group ID', max_length=24, unique=True)
	status = models.BooleanField(u'Status', default=True)
	def __str__(self):
		return self.gid
class UsersModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_users"
		verbose_name='Users'
		verbose_name_plural=verbose_name
	uid = models.CharField(u'User ID', max_length=24, unique=True)
	gid = models.ForeignKey(GroupsModel, verbose_name=u'Group ID')
	username = models.CharField(u'Username', max_length=24)
	password = models.CharField(u'Password', max_length=24)
	parameters = models.TextField(u'Parameters')
	user = models.ForeignKey(User, verbose_name=u"Related User")
	def __str__(self):
		return self.uid
class HTTPccmModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_httpccm"
		verbose_name='HTTP Client Connector'
		verbose_name_plural=verbose_name
	cid = models.CharField(u'Connector ID', max_length=24, unique=True, help_text='Connector identifier')
	url = models.CharField(u'URL', max_length=128, help_text='URL to be called with message parameters')
	method = models.CharField(u'Method', max_length=16, choices=(("GET", "GET",), ("POST", "POST",),))
	def __str__(self):
		return self.cid
class SMPPccmModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_smppccm"
		verbose_name = "SMPP Client Connector"
		verbose_name_plural=verbose_name
	cid = models.CharField(u'Connector ID', max_length=24, unique=True, help_text='Connector identifier')
	parameters = models.TextField(u'Parameters')
	action = models.BooleanField(u"Action", default=True, help_text='Start/Stop SMPP Connector')
	def __str__(self):
		return self.cid
morouter_types = (("DefaultRoute", "DefaultRoute",), ("StaticMORoute", "StaticMORoute",), ("RandomRoundrobinMORoute", "RandomRoundrobinMORoute",),)
class MORoutersModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_morouters"
		verbose_name='MO Router'
		verbose_name_plural=verbose_name
	type = models.CharField(u'Type', choices=morouter_types, max_length=24)
	order = models.CharField(u'Order', max_length=24, help_text='Router order, also used to identify router')
	smppconnectors = models.ForeignKey(SMPPccmModel, verbose_name=u'SMPP Connectors')
	httpconnectors = models.ForeignKey(HTTPccmModel, verbose_name=u'SMPP Connectors')
	filters = models.ForeignKey(FiltersModel, verbose_name=u'Filters')
mtrouter_types = (("DefaultRoute", "DefaultRoute",), ("StaticMTRoute", "StaticMTRoute",), ("RandomRoundrobinMTRoute", "RandomRoundrobinMTRoute",),)
class MTRoutersModel(TimeStampedModel):
	class Meta:
		db_table = "tbl_mtrouters"
		verbose_name='MT Router'
		verbose_name_plural=verbose_name
	type = models.CharField(u'Type', choices=mtrouter_types, max_length=24)
	order = models.CharField(u'Order', max_length=24, help_text='Router order, also used to identify router')
	rate = models.FloatField(u'Rate', default=0.1)
	smppconnectors = models.ForeignKey(SMPPccmModel, verbose_name=u'SMPP Connectors')
	httpconnectors = models.ForeignKey(HTTPccmModel, verbose_name=u'SMPP Connectors')
	filters = models.ForeignKey(FiltersModel, verbose_name=u'Filters')