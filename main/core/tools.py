import logging
import re
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


def table_rows(output):
    """Return the data rows of a jcli ``-l`` listing.

    Listings start with a ``#`` header line, then one ``#``-prefixed line per object and a
    ``Total ...`` footer. The ``#`` is stripped from the returned rows.
    """
    rows = [line for line in output.split('\n') if line.startswith('#')]
    return [row[1:] for row in rows[1:]]


_CONNECTORS = r'((?:(?:smppc|smpps|http)\([^)]*\)(?:,\s*)?)+)'
# order, type, [rate [(!)]], connector(s), filter(s), e.g.
# "20  RandomRoundrobinMTRoute  1.50000  smppc(c1), smppc(c2)  <U (uid=u1)>, <T>"
_MT_ROUTE_ROW_RE = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)(?:\s+\(!\))?\s+' + _CONNECTORS + r'\s*(.*)$')
_MO_ROUTE_ROW_RE = re.compile(r'^(\S+)\s+(\S+)\s+' + _CONNECTORS + r'\s*(.*)$')
def split_filters(text):
    """Split a route's ``<T>, <U (uid=u1)>`` filter list.

    Only commas outside parentheses separate filters: a ShortMessageFilter regex such as
    ``<SM (msg=^hello, <world>$)>`` contains commas of its own.
    """
    filters, current, depth = [], [], 0
    for char in text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth = max(depth - 1, 0)
        if char == ',' and depth == 0:
            filters.append(''.join(current))
            current = []
        else:
            current.append(char)
    filters.append(''.join(current))
    return [f.strip() for f in filters if f.strip()]


def parse_route_row(row, rated):
    """Parse one ``mtrouter -l`` (``rated=True``) or ``morouter -l`` row, or return None."""
    match = (_MT_ROUTE_ROW_RE if rated else _MO_ROUTE_ROW_RE).match(row.strip())
    if not match:
        return None
    groups = list(match.groups())
    route = {'order': groups.pop(0), 'type': groups.pop(0)}
    if rated:
        route['rate'] = groups.pop(0)
    connectors, filters = groups
    route['connectors'] = [c.strip() for c in connectors.split(',') if c.strip()]
    route['filters'] = split_filters(filters)
    return route


def as_list(value):
    """Accept a list (multi-select, JSON array) or a comma-separated string."""
    if value is None:
        return []
    if isinstance(value, str):
        value = value.split(',')
    return [str(v).strip() for v in value if str(v).strip()]


def json_errors(view_func):
    """Return Jasmin and unexpected failures as ``{"message", "status"}`` JSON for the UI."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except APIException as e:
            return JsonResponse({'message': str(e.detail), 'status': e.status_code}, status=e.status_code)
        except Exception:
            logger.exception('Unhandled error in %s', request.path)
            return JsonResponse({
                'message': _('Unexpected server error, check the panel logs for details.'),
                'status': 500,
            }, status=500)
    return _wrapped_view


def _ajax_only(methods):
    def decorator(view_func):
        @wraps(view_func)
        @require_http_methods(methods)
        def _wrapped_view(request, *args, **kwargs):
            if request.headers.get('x-requested-with') != 'XMLHttpRequest':
                return JsonResponse({'message': 'This is an AJAX-only endpoint', 'status': 400}, status=400)
            if not request.user.is_authenticated:
                # A redirect to the login page would reach jQuery as an HTML "success".
                return JsonResponse({
                    'message': _('Your session has expired, please sign in again.'),
                    'status': 401,
                    'login_url': settings.LOGIN_URL,
                }, status=401)
            return json_errors(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return decorator


require_post_ajax = _ajax_only(["POST"])
require_get_ajax = _ajax_only(["GET"])
