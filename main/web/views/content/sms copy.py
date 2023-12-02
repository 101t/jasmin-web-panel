from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

import sys

import smpplib.gsm
import smpplib.client
import smpplib.consts
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
    client = smpplib.client.Client('172.22.0.31', 2775)
    client.set_message_sent_handler(sent_handler)
    client.set_message_received_handler(received_handler)
    client.connect()
    client.bind_transceiver(system_id='test', password='test')
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(sms)
    #logging.info('Sending SMS "%s" to %s' % (string, dest))
    for part in parts:
        pdu = client.send_message(
            source_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            source_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            source_addr="jasmin",
            dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            destination_addr=callee,
            short_message=part,
            data_coding=encoding_flag,
            #esm_class=msg_type_flag,
            esm_class=smpplib.consts.SMPP_MSGMODE_FORWARD,
            registered_delivery=False,
    )
    sleep(.2)
    try:
        client.read_once()
        res_stats = 200
    except Exception as e:
        res_message = str(e)
        rest_status = 500
        args['error'] = res_message
    sleep(.8)
    client.unbind()
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
