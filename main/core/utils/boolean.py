# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from dateutil.parser import parse
from decimal import Decimal
import json

def is_json(string):
    try:
        json.loads(string)
    except:
        return False
    return True
def is_int(string):
    try:
        int(string)
    except:
        return False
    return True
def is_float(string):
    try:
        float(string)
    except:
        return False
    return True
def is_decimal(string):
    try:
        Decimal(string)
    except:
        return False
    return True

def is_date(string):
    try:
        parse(string)
        return True
    except:
        return False