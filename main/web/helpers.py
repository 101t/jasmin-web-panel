import logging
import urllib.error
import urllib.parse
import urllib.request

import smpplib.client
import smpplib.consts
import smpplib.gsm
from django.conf import settings

logger = logging.getLogger(__name__)


def sent_handler(pdu):
    logger.info(f'Sent seq={pdu.sequence} msgid={pdu.message_id}')


def received_handler(pdu):
    logger.info(f'Delivered seq={pdu.sequence} msgid={pdu.message_id}')


def send_smpp(src_addr, dst_addr, text):
    client = smpplib.client.Client(settings.TELNET_HOST, settings.TELNET_PORT)
    client.set_message_sent_handler(sent_handler)
    client.set_message_received_handler(received_handler)
    client.connect()
    client.bind_transceiver(system_id=settings.TELNET_USERNAME, password=settings.TELNET_PW)
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(text)

    for part in parts:
        pdu = client.send_message(
            source_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            source_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            source_addr=src_addr,
            dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            destination_addr=dst_addr,
            short_message=part,
            data_coding=encoding_flag,
            # esm_class=msg_type_flag,
            esm_class=smpplib.consts.SMPP_MSGMODE_FORWARD,
            registered_delivery=False,
        )
    try:
        client.read_once()
        res_status, res_message = 200, "OK"
    except Exception as e:
        res_status, res_message = 400, f"{e}"
    finally:
        client.unbind()
    return res_status


def send_http(src_addr, dst_addr, text):
    params = {
        'username': settings.TELNET_USERNAME,
        'password': settings.TELNET_PW,
        'from': src_addr,
        'to': dst_addr,
        'content': text
    }
    encoded_params = urllib.parse.urlencode(params)
    req = urllib.request.urlopen(
        f"{settings.HTTP_HOST}:{settings.HTTP_PORT}/send?{encoded_params}"
    )
    res_status, res_message = req.getcode(), req.read().decode('utf-8')
    return res_status, res_message
