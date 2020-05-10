from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .exceptions import TelnetUnexpectedResponse, TelnetConnectionTimeout, TelnetLoginFailed

import logging
import pexpect, sys, time

logger = logging.getLogger(__name__)

class TelnetConnectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Add a telnet connection to all request paths that start with /api/
        assuming we only need to connect for these means we avoid unecessary
        overhead on any other functionality we add, and keeps URL path clear
        for it.
        """
        # if not request.path.startswith('/api/'):
        #     return None
        if not request.path.endswith('/manage/'):
            return None
        try:
            # telnet = pexpect.spawn(
            #     "telnet %s %s" %
            #     (settings.TELNET_HOST, settings.TELNET_PORT),
            #     timeout=settings.TELNET_TIMEOUT,
            # )
            telnet = pexpect.spawn('telnet', [settings.TELNET_HOST, str(settings.TELNET_PORT)], timeout=settings.TELNET_TIMEOUT)
            #telnet.logfile_read = sys.stdout
            telnet.expect(':')
            telnet.sendline(settings.TELNET_USERNAME)
            telnet.expect(':')
            telnet.sendline(settings.TELNET_PW)
            #telnet.send("\r\n")
        except pexpect.EOF:
            logger.error("TelnetUnexpectedResponse")
            #raise TelnetUnexpectedResponse
        except pexpect.TIMEOUT:
            logger.error("TelnetConnectionTimeout")
            #raise TelnetConnectionTimeout

        try:
            telnet.expect_exact(settings.STANDARD_PROMPT)
        except pexpect.EOF:
            logger.error("TelnetLoginFailed")
            #raise TelnetLoginFailed
        else:
            request.telnet = telnet
            return None
    def process_response(self, request, response):
        "Make sure telnet connection is closed when unleashing response back to client"
        if hasattr(request, 'telnet'):
            try:
                request.telnet.sendline('quit')
            except pexpect.ExceptionPexpect:
                request.telnet.kill(9)
        return response