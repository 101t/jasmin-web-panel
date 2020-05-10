from django.conf import settings

import pexpect

from ..exceptions import TelnetUnexpectedResponse, TelnetConnectionTimeout, TelnetLoginFailed

class TelnetConnection(object):
    def __init__(self):
        try:
            telnet = pexpect.spawn("telnet %s %s" % (settings.TELNET_HOST, settings.TELNET_PORT), timeout=settings.TELNET_TIMEOUT,)
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
            self.telnet = telnet
    def __del__(self):
        "Make sure telnet connection is closed when unleashing response back to client"
        try:
            self.telnet.sendline('quit')
        except pexpect.ExceptionPexpect:
            self.telnet.kill(9)