from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

import sys

import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error

from time import sleep
import json

from main.core.smpp import HTTPCCM

def send_message(dest, string):
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(string)

    #logging.info('Sending SMS "%s" to %s' % (string, dest))
    for part in parts:
        pdu = client.send_message(
            source_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            source_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            source_addr="jasmin",
            dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            destination_addr=dest,
            short_message=part,
            data_coding=encoding_flag,
            #esm_class=msg_type_flag,
            esm_class=smpplib.consts.SMPP_MSGMODE_FORWARD,
            registered_delivery=False,
    )
    #logging.debug(pdu.sequence)


def received_handler(pdu):
    print ('* delivered {}'.format(pdu.sequence))

def sent_handler(pdu):
    print ('* sent seq={}   msgid={}'.format(pdu.sequence, pdu.message_id))
    
@login_required
def send_sms_view(request):
    return render(request, "web/content/send_sms.html")


@login_required
def send_sms_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    args['msisdn'] = request.POST.get("msisdn")
    args['sms'] = request.POST.get("sms")
    callee = request.POST.get("msisdn")
    sms = request.POST.get("sms")
    baseParams = {'username':'foo', 'password':'bar', 'from': 'jasmin', 'to': callee, 'content': sms}
    res = urllib.request.urlopen("http://172.22.0.4:1401/send?%s" % urllib.parse.urlencode(baseParams)).read().decode('utf-8')
    res_status = 200
    args['result'] = res
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
