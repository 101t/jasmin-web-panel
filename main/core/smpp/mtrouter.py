import logging
import random
from collections import OrderedDict
from typing import List

from django.conf import settings

from main.core.exceptions import (
    JasminError,
    UnknownError, MissingKeyError,
    MultipleValuesRequiredKeyError, ObjectNotFoundError
)
from main.core.utils import is_float, is_int
from main.core.tools import set_ikeys, split_cols
from .conn import TelnetConnection

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)


class MTRouter(TelnetConnection):
    """MTRouter for managing MT Routes"""
    lookup_field = 'order'
    available_actions = ['list', 'add', 'delete']

    MT_ROUTER_TYPES = (
        ('DefaultRoute', 'Default Route'),
        ('StaticMTRoute', 'Static MT Route'),
        ('RandomRoundrobinMTRoute', 'Random Roundrobin MT Route'),
        ('FailoverMTRoute', 'Failover MT Route'),
    )

    def _list(self) -> List[dict]:
        """List MT router as python dict"""
        self.telnet.sendline('mtrouter -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        if len(result) < 3:
            return []
        results = [s.replace(', ', ',').replace('(!)', '') for s in result[2:-2] if s]
        routers = split_cols(results)
        return [
            {
                'order': r[0].strip().lstrip('#'),
                'type': r[1],
                'rate': r[2],
                'connectors': [c.strip() for c in r[3].split(',')],
                'filters': [c.strip() for c in ' '.join(r[4:]).split(',')] if len(r) > 3 else []
            } for r in routers
        ]

    def list(self):
        """List MT Routers. No parameters"""
        return {"mtrouters": self._list()}

    def get_router(self, order):
        """Return data for one mtrouter as Python dict"""
        routers = self._list()
        try:
            return {'mtrouter': next(m for m in routers if m['order'] == order)}
        except (StopIteration, IndexError):
            raise ObjectNotFoundError('No MTRouter with order: %s' % order)

    def router_exists(self, order: str) -> bool:
        routers = self._list()
        return any(m['order'] == order for m in routers)

    def retrieve(self, order):
        """Details for one MTRouter by order (integer)"""
        return self.get_router(order)

    def flush(self):
        """Flush entire routing table"""
        self.telnet.sendline('mtrouter -f')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        self.telnet.sendline('persist')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'mtrouters': []}

    def create(self, data):
        """Add a new MTRouter"""
        route_type = data.get('type') or "DefaultRoute"
        order = data.get('order') or "1"
        filters = data.get('filters') or ""
        rate = data.get('rate') or "0.0"
        """ MT Router only support SMPP connectors, HTTP not allowed """
        smppconnectors = data.get('smppconnectors') or ""
        
        if self.router_exists(order):
            raise MultipleValuesRequiredKeyError('Order %s already exists' % order)

        self.telnet.sendline('mtrouter -a')
        self.telnet.expect(r'Adding a new MT Route(.+)\n' + INTERACTIVE_PROMPT)
        
        ikeys = OrderedDict({
            'type': route_type,
            'order': order if is_int(order) else str(random.randrange(1, 99)),
            'rate': str(float(rate)) if is_float(rate) else "0.0",
        })

        if route_type != 'DefaultRoute':
            if not filters:
                raise MissingKeyError('%s router requires filters' % route_type)
            filters = filters.split(',')
            ikeys['filters'] = ';'.join(filters)
        
        connectors = ['smppc(%s)' % c.strip() for c in smppconnectors.split(',') if c.strip()]
        if route_type == 'RandomRoundrobinMTRoute':
            if len(connectors) < 2:
                raise MultipleValuesRequiredKeyError('Round Robin route requires at least two connectors')
            ikeys['connectors'] = ';'.join(connectors)
        elif route_type == 'FailoverMTRoute':
            if len(connectors) < 2:
                raise MultipleValuesRequiredKeyError('FailOver route requires at least two connectors')
            ikeys['connectors'] = ';'.join(connectors)
        else:
            if len(connectors) != 1:
                raise MissingKeyError('One and only one connector required')
            ikeys['connector'] = connectors[0]
        
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
