from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from .exceptions import TelnetUnexpectedResponse, TelnetConnectionTimeout, TelnetLoginFailed
from .utils import get_user_agent, get_client_ip, LazyEncoder
from .models import ActivityLog

import logging
import pexpect
import json

logger = logging.getLogger(__name__)

def is_ajax(request):
    """Check if the request is an AJAX request."""
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

class AjaxMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_ajax = is_ajax(request)
        response = self.get_response(request)
        return response

class TelnetConnectionMiddleware(MiddlewareMixin):
    """Middleware to manage a Telnet connection."""

    def add_telnet_connection(self, request):
        """Attempt to establish a telnet connection."""
        telnet = pexpect.spawn('telnet', [settings.TELNET_HOST, str(settings.TELNET_PORT)], timeout=settings.TELNET_TIMEOUT)
        try:
            telnet.expect(':')
            telnet.sendline(settings.TELNET_USERNAME)
            telnet.expect(':')
            telnet.sendline(settings.TELNET_PW)
            telnet.expect_exact(settings.STANDARD_PROMPT)
        except (pexpect.EOF, pexpect.TIMEOUT, AttributeError) as e:
            logger.error(f"Telnet connection error: {str(e)}")
            telnet = None
        return telnet

    def process_request(self, request):
        if request.path.startswith('/api/') and not request.path.endswith('/manage/'):
            request.telnet = self.add_telnet_connection(request)
        else:
            request.telnet = None

    def process_response(self, request, response):
        if hasattr(request, 'telnet') and request.telnet:
            try:
                request.telnet.sendline('quit')
                request.telnet.expect_exact(settings.STANDARD_PROMPT)
            except pexpect.ExceptionPexpect:
                request.telnet.kill(9)
            finally:
                request.telnet.close()
        return response

class UserAgentMiddleware(MiddlewareMixin):
    """Middleware to process the user agent."""

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def clean_params(self, params):
        """Clean the parameters by removing specific keys."""
        params = params.copy()
        params.pop("csrfmiddlewaretoken", None)
        params.pop("s", None)
        return params

    def process_request(self, request):
        user_agent = get_user_agent(request)
        if request.user.is_authenticated and is_ajax(request) and request.path.endswith('/manage/'):
            params = self.clean_params(request.POST or request.GET or {})
            ActivityLog.objects.create(
                user=request.user,
                service=request.POST.get("s", "unknown"),
                method=request.method,
                params=json.dumps(params, cls=LazyEncoder),
                path=request.path,
                ip=get_client_ip(request),
                user_agent=json.dumps(user_agent.__dict__ or {}, cls=LazyEncoder),
            )