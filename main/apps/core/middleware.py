import pexpect

from django.conf import settings

from .exceptions import TelnetUnexpectedResponse, TelnetConnectionTimeout, TelnetLoginFailed
from django.utils.deprecation import MiddlewareMixin
class TelnetConnectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Add a telnet connection to all request paths that start with /api/
        assuming we only need to connect for these means we avoid unecessary
        overhead on any other functionality we add, and keeps URL path clear
        for it.
        """
        if not request.path.startswith('/api/'):
            return None
        try:
            telnet = pexpect.spawn(
                "telnet %s %s" %
                (settings.TELNET_HOST, settings.TELNET_PORT),
                timeout=settings.TELNET_TIMEOUT,
            )
            telnet.expect_exact('Username: ')
            telnet.sendline(settings.TELNET_USERNAME)
            telnet.expect_exact('Password: ')
            telnet.sendline(settings.TELNET_PW)
        except pexpect.EOF:
            raise TelnetUnexpectedResponse
        except pexpect.TIMEOUT:
            raise TelnetConnectionTimeout

        try:
            telnet.expect_exact(settings.STANDARD_PROMPT)
        except pexpect.EOF:
            raise TelnetLoginFailed
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
