# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.template.loader import render_to_string
from django.conf import settings

from main.core.mailer import PyMail, PyMailMultiPart
from main.taskapp.celery import app

"""
kwargs = {
    user        : {"username": "joe_user", "email": "joe@gmail.com", "name": "Joe Life"},
    site_name   : "My Company",
    logo_url    : "http://www.g.com/logo.png",
    site_url    : "http://www.g.com",
    logo        : '<img data-imagetype="External" alt="{}" src="{}{}" height="100">'.format(site_url, site_url, logo_url)
}

"""

@app.task
def mail_html_maillist(maillist, subject, html_template, kwargs={}, lang=settings.LANGUAGE_CODE,):
    translation.activate(lang)
    mail = PyMailMultiPart(subject=subject, html_template=html_template,)
    mail.send(maillist=maillist, kwargs=kwargs)

@app.task
def mail_html_envelopes(envelopes, subject, html_template, lang=settings.LANGUAGE_CODE,):
    '''
    e.g envelopes = {"name": "Joe Life", "email": "info@domain.com", "kwargs": "Dictionary of extra"}
    '''
    translation.activate(lang)
    mail = PyMailMultiPart(subject=subject, html_template=html_template,)
    mail.send_envelopes(envelopes=envelopes)