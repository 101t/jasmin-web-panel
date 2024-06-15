import logging
import random
from collections import OrderedDict

from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError

from main.core.exceptions import (
    JasminError,
    UnknownError, MissingKeyError,
    MultipleValuesRequiredKeyError, ObjectNotFoundError
)
from main.core.utils import is_float, is_int
from main.core.tools import set_ikeys, split_cols

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)


class MTRouter(object):
    """MTRouter for managing MT Routes"""
    lookup_field = 'order'

    def __init__(self, telnet):
        self.telnet = telnet

    def _list(self):
        """List MT router as python dict"""
        self.telnet.sendline('mtrouter -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        if len(result) < 3:
            return {'mtrouters': []}
        results = [s.replace(', ', ',').replace('(!)', '') for s in result[2:-2] if s]
        routers = split_cols(results)
        return {
            'mtrouters':
                [
                    {
                        'order': r[0].strip().lstrip('#'),
                        'type': r[1],
                        'rate': r[2],
                        'connectors': [c.strip() for c in r[3].split(',')],
                        'filters': [c.strip() for c in ' '.join(r[4:]).split(',')] if len(r) > 3 else []
                    } for r in routers
                ]
        }

    def list(self):
        """List MT Routers. No parameters"""
        return self._list()

    def get_router(self, order):
        """Return data for one mtrouter as Python dict"""
        routers = self._list()['mtrouters']
        try:
            return {'mtrouter': next(m for m in routers if m['order'] == order)}
        except StopIteration:
            raise ObjectNotFoundError('No MTRouter with order: %s' % order)

    def retrieve(self, order):
        """Details for one MTRouter by order (integer)"""
        return self.get_router(order)

    # methods=['delete']
    def flush(self):
        """Flush entire routing table"""
        self.telnet.sendline('mtrouter -f')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        self.telnet.sendline('persist')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'mtrouters': []}

    def create(self, data):
        """Create MTRouter.
        Required parameters: type, order, smppconnectors, httpconnectors
        More than one connector is allowed only for RandomRoundrobinMTRoute and FailoverMTRoute
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: type
          description: One of DefaultRoute, StaticMTRoute, RandomRoundrobinMTRoute, FailoverMTRoute
          required: true
          type: string
          paramType: form
        - name: order
          description: Router order, also used to identify router
          required: true
          type: string
          paramType: form
        - name: rate
          description: Router rate, may be zero for free
          required: true
          type: float
          paramType: form
        - name: smppconnectors
          description: List of SMPP connector ids.
          required: false
          type: array
          paramType: form
        - name: httpconnectors
          description: List of HTTP connector ids.
          required: false
          type: array
          paramType: form
        - name: filters
          description: List of filters, required except for DefaultRoute
          required: false
          type: array
          paramType: form
        """
        try:
            route_type, order, rate = data.get("type"), data.get("order"), data.get("rate")
            self.retrieve(order)
        except Exception:  # noqa
            route_type, order, rate = "defaultroute", "1", "0.0"
        else:
            raise MissingKeyError('MT route already exists')
        # raise MissingKeyError('Missing parameter: type or order required')
        route_type = route_type.lower()
        self.telnet.sendline('mtrouter -a')
        self.telnet.expect(r'Adding a new MT Route(.+)\n' + INTERACTIVE_PROMPT)
        ikeys = OrderedDict({'type': route_type})
        if route_type != 'defaultroute':
            try:
                filters = data['filters'] or ""
                filters = filters.split(',')
            except MultiValueDictKeyError:
                raise MissingKeyError('%s router requires filters' % route_type)
            ikeys['filters'] = ';'.join(filters)
        ikeys['order'] = order if is_int(order) else str(random.randrange(1, 99))
        smppconnectors = data.get('smppconnectors') or ""
        """ MT Router only support SMPP connectors, HTTP not allowed """
        # httpconnectors = data.get('httpconnectors') or ""
        connectors = ['smppc(%s)' % c.strip()
                      for c in smppconnectors.split(',') if c.strip()
                      ]  # + ['http(%s)' % c for c in httpconnectors.split(',') if c.strip()]
        if route_type == 'randomroundrobinmtroute':
            if len(connectors) < 2:
                raise MultipleValuesRequiredKeyError('Round Robin route requires at least two connectors')
            ikeys['connectors'] = ';'.join(connectors)
        elif route_type == 'failovermtroute':
            if len(connectors) < 2:
                raise MultipleValuesRequiredKeyError('FailOver route requires at least two connectors')
            ikeys['connectors'] = ';'.join(connectors)
        else:
            if len(connectors) != 1:
                raise MissingKeyError('One and only one connector required')
            ikeys['connector'] = connectors[0]
        ikeys['rate'] = str(float(rate)) if is_float(rate) else "0.0"
        set_ikeys(self.telnet, ikeys)
        self.telnet.sendline('persist')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'mtrouter': self.get_router(order)}

    def simple_mtrouter_action(self, action, order, return_mtroute=True):
        self.telnet.sendline('mtrouter -%s %s' % (action, order))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown MT Route: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist')
            if return_mtroute:
                self.telnet.expect(r'.*' + STANDARD_PROMPT)
                return {'mtrouter': self.get_router(order)}
            else:
                return {'order': order}
        elif matched_index == 1:
            raise UnknownError(detail='No router:' + order)
        else:
            raise JasminError(self.telnet.match.group(1))

    def destroy(self, order):
        """Delete a mtrouter. One parameter required, the router identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent router
        - 400: other error
        """
        return self.simple_mtrouter_action('r', order, return_mtroute=False)
