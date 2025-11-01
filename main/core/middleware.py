from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.db import transaction, connection
from .utils import get_user_agent, get_client_ip, LazyEncoder
from .models import ActivityLog

import logging
import pexpect
import json

logger = logging.getLogger(__name__)


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
        # Check if we need to process the request (check the path or other conditions)
        if self.should_process_request(request):
            self.process_request(request)
        return self.get_response(request)

    def should_process_request(self, request):
        # Add logic to decide if the request should be processed
        return request.user.is_authenticated and request.path.endswith('/manage/')

    def process_request(self, request):
        cached_user_agent = cache.get('user_agent_' + request.META['HTTP_USER_AGENT'])
        if not cached_user_agent:
            user_agent = get_user_agent(request)
            cache.set('user_agent_' + request.META['HTTP_USER_AGENT'], user_agent, 120)  # Cache for 2 minutes
        else:
            user_agent = cached_user_agent

        self._enqueue_activity_log_creation(request, user_agent)

    def _enqueue_activity_log_creation(self, request, user_agent):
        # Extract data from request before threading to avoid context issues
        log_data = {
            'user_id': request.user.id,
            'service': request.POST.get("s", "unknown"),
            'method': request.method,
            'params': self.clean_params(request.POST or request.GET or {}),
            'path': request.path,
            'ip': get_client_ip(request),
            'user_agent': user_agent,
        }
        
        # Use threading.Thread instead of ThreadPoolExecutor for simpler lifecycle
        import threading
        thread = threading.Thread(target=self._create_activity_log_safe, args=(log_data,), daemon=True)
        thread.start()

    def clean_params(self, params):
        """Clean sensitive parameters before logging."""
        cleaned = dict(params)
        sensitive_keys = ['password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey']
        for key in list(cleaned.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                cleaned[key] = '***REDACTED***'
        return cleaned

    def _create_activity_log_safe(self, log_data):
        """Thread-safe activity log creation with proper DB connection handling."""
        try:
            self._create_activity_log(log_data)
        except Exception as e:
            logger.error(f"Failed to create activity log: {str(e)}", exc_info=True)
        finally:
            # Close database connection for this thread
            connection.close()
    
    @transaction.atomic
    def _create_activity_log(self, log_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=log_data['user_id'])
        activity_log = ActivityLog(
            user=user,
            service=log_data['service'],
            method=log_data['method'],
            params=json.dumps(log_data['params'], cls=LazyEncoder),
            path=log_data['path'],
            ip=log_data['ip'],
            user_agent=json.dumps(log_data['user_agent'].__dict__ or {}, cls=LazyEncoder),
        )
        activity_log.save()
