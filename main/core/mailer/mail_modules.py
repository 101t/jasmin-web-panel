"""
Python 2
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
"""
from typing import List

from django.template.loader import render_to_string

from main.core.models import EmailServer

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class PyMail(object):
    def __init__(self, subject, from_mail, mails, message):
        self.subject = str(subject)
        self.from_mail = from_mail
        self.mails = mails
        self.message = str(message)
        self.email_server = EmailServer.objects.get(active=True)

    def send(self):
        mailserver = None
        if self.email_server:
            if not self.from_mail:
                self.from_mail = self.email_server.username
            if self.email_server.ssl:
                # identify ourselves to smtp gmail client
                mailserver = smtplib.SMTP_SSL(self.email_server.server, self.email_server.port)
                # re-identify ourselves as an encrypted connection
                mailserver.ehlo()
            else:
                mailserver = smtplib.SMTP(self.email_server.server, self.email_server.port)
                mailserver.starttls()
            # mailserver.login(django_settings.EMAIL_HOST_USER, django_settings.EMAIL_HOST_PASSWORD)
            mailserver.login(self.email_server.username, self.email_server.password)
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
        self.subject = str(subject)
        self.email_server = EmailServer.objects.get(active=True)
        self.from_mail = self.email_server.username
        self.html_template = html_template

    def named(self, mail, name=""):
        return "{0} <{1}>".format(name, mail) if name else mail

    def send(self, mails: list, kwargs=None):
        if kwargs is None:
            kwargs = {}
        if self.email_server:
            msg = MIMEMultipart('related', type="text/html")
            msg["Subject"] = self.subject
            msg["From"] = self.from_mail
            html_part = MIMEText(render_to_string(self.html_template, kwargs), 'html')
            msg.attach(html_part)
            if self.email_server.ssl:
                mail_obj = smtplib.SMTP_SSL(
                    host=self.email_server.server, port=self.email_server.port, timeout=120.0,
                )
                mail_obj.ehlo()
            else:
                mail_obj = smtplib.SMTP(
                    host=self.email_server.server, port=self.email_server.port, timeout=120.0,
                )
                mail_obj.starttls()
            mail_obj.login(self.email_server.username, self.email_server.password)
            for to_mail in mails:
                msg["To"] = to_mail
                mail_obj.sendmail(self.from_mail, to_mail, msg.as_string())
            mail_obj.quit()

    def send_envelopes(self, envelopes: dict):
        if self.email_server:
            if self.email_server.ssl:
                mail_obj = smtplib.SMTP_SSL(self.email_server.server, self.email_server.port)
                mail_obj.ehlo()
            else:
                mail_obj = smtplib.SMTP(self.email_server.server, self.email_server.port)
                mail_obj.starttls()
            mail_obj.login(self.email_server.username, self.email_server.password)
            for envelope in envelopes:
                msg = MIMEMultipart('related', type='text/html')
                msg["Subject"] = self.subject
                msg["From"] = self.from_mail
                html_part = MIMEText(render_to_string(self.html_template, envelope.get("kwargs")), 'html')
                msg.attach(html_part)
                msg["To"] = self.named(mail=envelope.get("email"), name=envelope.get("name"))
                mail_obj.sendmail(self.from_mail, envelope.get("email"), msg.as_string())
            mail_obj.quit()
