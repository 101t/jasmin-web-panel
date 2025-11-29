"""
SMS sending helpers for SMPP and HTTP protocols.
"""
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Tuple

import smpplib.client
import smpplib.consts
import smpplib.gsm
from django.conf import settings

logger = logging.getLogger(__name__)


def _sent_handler(pdu):
    """Handler for sent PDU messages."""
    logger.info(f'Sent seq={pdu.sequence} msgid={pdu.message_id}')


def _received_handler(pdu):
    """Handler for received PDU messages."""
    logger.info(f'Delivered seq={pdu.sequence} msgid={pdu.message_id}')


def send_smpp(
        src_addr: str,
        dst_addr: str,
        text: str,
        system_id: str = None,
        password: str = None
) -> Tuple[int, str]:
    """
    Send SMS via SMPP protocol.
    
    Args:
        src_addr: Source address (sender)
        dst_addr: Destination address (recipient)
        text: Message content
        system_id: SMPP system ID (defaults to settings.SMPP_SYSTEM_ID)
        password: SMPP password (defaults to settings.SMPP_PASSWORD)
    
    Returns:
        Tuple of (status_code, message)
    """
    system_id = system_id or settings.SMPP_SYSTEM_ID
    password = password or settings.SMPP_PASSWORD
    
    client = None
    try:
        client = smpplib.client.Client(settings.SMPP_HOST, settings.SMPP_PORT)
        client.set_message_sent_handler(_sent_handler)
        client.set_message_received_handler(_received_handler)
        client.connect()
        client.bind_transceiver(system_id=system_id, password=password)
        
        parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(text)
        
        for part in parts:
            client.send_message(
                source_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
                source_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
                source_addr=src_addr,
                dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
                dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
                destination_addr=dst_addr,
                short_message=part,
                data_coding=encoding_flag,
                esm_class=smpplib.consts.SMPP_MSGMODE_FORWARD,
                registered_delivery=False,
            )
        
        client.read_once()
        return 200, "OK"
    except smpplib.exceptions.ConnectionError as e:
        logger.error(f"SMPP Connection Error: {e}")
        return 400, f"Connection failed: {e}"
    except smpplib.exceptions.PDUError as e:
        logger.error(f"SMPP PDU Error: {e}")
        return 400, f"PDU Error: {e}"
    except Exception as e:
        logger.error(f"SMPP Error: {e}")
        return 400, str(e)
    finally:
        if client:
            try:
                client.unbind()
                client.disconnect()
            except Exception:
                pass


def send_http(
        src_addr: str,
        dst_addr: str,
        text: str,
        username: str = None,
        password: str = None
) -> Tuple[int, str]:
    """
    Send SMS via HTTP protocol.
    
    Args:
        src_addr: Source address (sender)
        dst_addr: Destination address (recipient)
        text: Message content
        username: HTTP username (defaults to settings.HTTP_USERNAME)
        password: HTTP password (defaults to settings.HTTP_PASSWORD)
    
    Returns:
        Tuple of (status_code, message)
    """
    username = username or settings.HTTP_USERNAME
    password = password or settings.HTTP_PASSWORD
    
    params = {
        'username': username,
        'password': password,
        'from': src_addr,
        'to': dst_addr,
        'content': text
    }
    encoded_params = urllib.parse.urlencode(params)
    url = f"{settings.HTTP_HOST}:{settings.HTTP_PORT}/send?{encoded_params}"
    
    try:
        req = urllib.request.urlopen(url, timeout=30)
        return req.getcode(), req.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f"HTTP Error {e.code}: {error_body}")
        return e.code, error_body
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        return 400, f"Connection failed: {e.reason}"
    except Exception as e:
        logger.error(f"HTTP Send Error: {e}")
        return 400, str(e)
