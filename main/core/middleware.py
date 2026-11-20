from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import logging

from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.db import transaction, connection
from .utils import get_user_agent, get_client_ip, LazyEncoder
from .models import ActivityLog

logger = logging.getLogger(__name__)
_ACTIVITY_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="activity-log")


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
        user_agent_header = request.META.get('HTTP_USER_AGENT', '')
        if user_agent_header:
            ua_hash = hashlib.sha256(user_agent_header.encode('utf-8', 'ignore')).hexdigest()[:32]
            cache_key = f'user_agent_{ua_hash}'
            cached_user_agent = cache.get(cache_key)
            if not cached_user_agent:
                user_agent = get_user_agent(request)
                cache.set(cache_key, user_agent, 120)  # Cache for 2 minutes
            else:
                user_agent = cached_user_agent
        else:
            user_agent = get_user_agent(request)

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

        _ACTIVITY_EXECUTOR.submit(self._create_activity_log_safe, log_data)

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
