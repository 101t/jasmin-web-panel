from typing import List
from django.utils import translation
# from django.template.loader import render_to_string
from django.conf import settings

from main.core.mailer import PyMail, PyMailMultiPart
from config.celery import app


@app.task(bind=True)
def mail_html_mails(self, mails: List[str], subject: str, html_template: str, kwargs=None,
                    lang: str = settings.LANGUAGE_CODE):
    if kwargs is None:
        kwargs = {}
    translation.activate(lang)
    mail = PyMailMultiPart(subject=subject, html_template=html_template, )
    mail.send(mails=mails, kwargs=kwargs)


@app.task(bind=True)
def mail_html_envelopes(self, envelopes, subject: str, html_template: str, lang: str = settings.LANGUAGE_CODE):
    """
    e.g envelopes = {"name": "Joe Life", "email": "info@domain.com", "kwargs": "Dictionary of extra"}

    kwargs = {
        users        : {"username": "joe_user", "email": "joe@gmail.com", "name": "Joe Life"},
        site_name   : "My Company",
        logo_url    : "http://www.g.com/logo.png",
        site_url    : "http://www.g.com",
        logo        : '<img data-imagetype="External" alt="{}" src="{}{}" height="100">'.format(site_url, site_url, logo_url)
    }
    """
    translation.activate(lang)
    mail = PyMailMultiPart(subject=subject, html_template=html_template, )
    mail.send_envelopes(envelopes=envelopes)
