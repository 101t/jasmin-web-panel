# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.template.loader import render_to_string
from django.conf import settings as django_settings
from django.utils.translation import gettext_lazy as _

from main.core.models import EmailServer

import smtplib, re, os, imghdr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
'''
Python 2
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
'''

class PyMail(object):
	def __init__(self, subject, from_mail, maillist, message):
		self.subject 		= str(subject)
		self.from_mail 		= from_mail
		self.maillist 		= maillist
		self.message 		= str(message)
		self.emailserver 	= EmailServer.objects.filter(active=True).first()
	def send(self):
		mailserver = None
		if self.emailserver:
			if not self.from_mail:
				self.from_mail = self.emailserver.username
			if self.emailserver.ssl:
				# identify ourselves to smtp gmail client
				mailserver = smtplib.SMTP_SSL(self.emailserver.server, self.emailserver.port)
				# re-identify ourselves as an encrypted connection
				mailserver.ehlo()
			else:
				mailserver = smtplib.SMTP(self.emailserver.server, self.emailserver.port)
				mailserver.starttls()
				#mailserver.login(django_settings.EMAIL_HOST_USER, django_settings.EMAIL_HOST_PASSWORD)
			mailserver.login(self.emailserver.username, self.emailserver.password)
			for mail in self.maillist:
				message = """\
From: %s
To: %s
Subject: %s

%s
""" % (self.from_mail, mail, self.subject, self.message)
				# print(self.from_mail)
				# print(message)
				mailserver.sendmail(self.from_mail, mail, message.encode("utf8"))
			mailserver.close()

class PyMailMultiPart(object):
	def __init__(self, subject, html_template="core/email/email_sample.html"):
		self.subject 	= str(subject)
		self.emailserver = EmailServer.objects.filter(active=True).first()
		self.from_mail 		= self.emailserver.username
		self.html_template 	= html_template
	def named(self, mail, name=""):
		return "{0} <{1}>".format(name, mail) if name else mail
	def send(self, maillist=[], kwargs={}):
		mailobject = None
		if self.emailserver:
			msg = MIMEMultipart('related', type="text/html")
			msg["Subject"] = self.subject
			msg["From"] = self.from_mail
			htmlpart = MIMEText(render_to_string(self.html_template, kwargs), 'html')
			msg.attach(htmlpart)
			if self.emailserver.ssl:
				mailobject = smtplib.SMTP_SSL(self.emailserver.server, self.emailserver.port)
				mailobject.ehlo()
			else:
				mailobject = smtplib.SMTP(self.emailserver.server, self.emailserver.port)
				mailobject.starttls()
			mailobject.login(self.emailserver.username, self.emailserver.password)
			for to_mail in maillist:
				msg["To"] = to_mail
				mailobject.sendmail(self.from_mail, to_mail, msg.as_string())
			mailobject.quit()
	def send_envelopes(self, envelopes=[]):
		mailobject = None
		if self.emailserver:
			if self.emailserver.ssl:
				mailobject = smtplib.SMTP_SSL(self.emailserver.server, self.emailserver.port)
				mailobject.ehlo()
			else:
				mailobject = smtplib.SMTP(self.emailserver.server, self.emailserver.port)
				mailobject.starttls()
			mailobject.login(self.emailserver.username, self.emailserver.password)
			for enve in envelopes:
				msg = MIMEMultipart('related', type='text/html')
				msg["Subject"] = self.subject
				msg["From"] = self.from_mail
				htmlpart = MIMEText(render_to_string(self.html_template, enve.get("kwargs")), 'html')
				msg.attach(htmlpart)
				msg["To"] = self.named(mail=enve.get("email"), name=enve.get("name"))
				mailobject.sendmail(self.from_mail, enve.get("email"), msg.as_string())
			mailobject.quit()