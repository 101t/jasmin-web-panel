from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from .exceptions import TelnetUnexpectedResponse, TelnetConnectionTimeout, TelnetLoginFailed
from .utils import get_user_agent, get_client_ip, LazyEncoder
from .models import ActivityLog

import logging
import pexpect, sys, time, json

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
            telnet = pexpect.spawn('telnet', [settings.TELNET_HOST, str(settings.TELNET_PORT)],
                                   timeout=settings.TELNET_TIMEOUT)
            # telnet.logfile_read = sys.stdout
            telnet.expect(':')
            telnet.sendline(settings.TELNET_USERNAME)
            telnet.expect(':')
            telnet.sendline(settings.TELNET_PW)
            # telnet.send("\r\n")
        except pexpect.EOF:
            logger.error("TelnetUnexpectedResponse")
            # raise TelnetUnexpectedResponse
        except pexpect.TIMEOUT:
            logger.error("TelnetConnectionTimeout")
            # raise TelnetConnectionTimeout
        except AttributeError as e:
            logger.error(f"The Jasmin SMS Gateway not configured properly, the error: \n {e}")

        try:
            telnet.expect_exact(settings.STANDARD_PROMPT)
        except pexpect.EOF:
            logger.error("TelnetLoginFailed")
            # raise TelnetLoginFailed
        except UnboundLocalError as e:
            logger.error(f"Cannot connect through Telnet, the error: \n {e}")
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


class UserAgentMiddleware(object):

    def __init__(self, get_response=None):
        if get_response is not None:
            self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        user_agent = get_user_agent(request)
        if request.user.is_authenticated and request.is_ajax() and request.path.endswith('/manage/'):
            def clean_params(params):
                params = params.copy()
                if "csrfmiddlewaretoken" in params:
                    params.pop("csrfmiddlewaretoken", None)
                if "s" in params:
                    params.pop("s", None)
                return params

            if request.POST.get("s") != "list":
                ActivityLog.objects.create(
                    user=request.user,
                    service=request.POST.get("s", "unknown"),
                    method=request.method,
                    params=json.dumps(clean_params(request.POST or request.GET or {}), cls=LazyEncoder),
                    path=request.path,
                    ip=get_client_ip(request),
                    user_agent=json.dumps(user_agent.__dict__ or {}, cls=LazyEncoder),
                )
