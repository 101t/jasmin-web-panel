import logging
from typing import List

from main.core.exceptions import (
    DuplicateEntryError,
    MissingKeyError,
    MultipleValuesRequiredKeyError,
    ObjectNotFoundError,
)
from main.core.utils import is_float, is_int
from main.core.tools import as_list, parse_route_row, table_rows
from .conn import TelnetConnection

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

    @staticmethod
    def parse_list(output) -> List[dict]:
        """Parse ``mtrouter -l`` output as a list of dicts"""
        routes = []
        for row in table_rows(output):
            route = parse_route_row(row, rated=True)
            if route is None:
                logger.warning('Unexpected MT route row: %r', row)
            else:
                routes.append(route)
        return routes

    def _list(self) -> List[dict]:
        """List MT router as python dict"""
        return self.parse_list(self.run_command('mtrouter -l'))

    def list(self):
        """List MT Routers. No parameters"""
        return {"mtrouters": self._list()}

    def get_router(self, order):
        """Return data for one mtrouter as Python dict"""
        try:
            return {'mtrouter': next(m for m in self._list() if m['order'] == str(order))}
        except StopIteration:
            raise ObjectNotFoundError('No MTRouter with order: %s' % order)

    def router_exists(self, order: str) -> bool:
        return any(m['order'] == str(order) for m in self._list())

    def retrieve(self, order):
        """Details for one MTRouter by order (integer)"""
        return self.get_router(order)

    def flush(self):
        """Flush entire routing table"""
        self.run_action('mtrouter -f')
        self.persist()
        return {'mtrouters': []}

    def create(self, data):
        """Add a new MTRouter

        ``smppconnectors`` and ``filters`` are lists of ids, or comma-separated strings.
        MT routes deliver through SMPP client connectors only (``smppc(cid)``).
        """
        route_type = data.get('type') or "DefaultRoute"
        # Jasmin always stores the DefaultRoute at order 0.
        order = "0" if route_type == 'DefaultRoute' else str(data.get('order') or '').strip()
        if not is_int(order) or int(order) < 0:
            raise MissingKeyError('Order must be a positive integer')
        rate = str(data.get('rate') or "0").strip()
        if not is_float(rate) or float(rate) < 0:
            raise MissingKeyError('Rate must be a positive number')
        filters = as_list(data.get('filters'))
        connectors = ['smppc(%s)' % c for c in as_list(data.get('smppconnectors'))]

        if self.router_exists(order):
            raise DuplicateEntryError('Order %s already exists' % order)

        lines = ['type %s' % route_type, 'order %s' % order, 'rate %s' % float(rate)]
        if route_type in ('RandomRoundrobinMTRoute', 'FailoverMTRoute'):
            if len(connectors) < 2:
                raise MultipleValuesRequiredKeyError('%s requires at least two connectors' % route_type)
            lines.append('connectors %s' % ';'.join(connectors))
        else:
            if len(connectors) != 1:
                raise MissingKeyError('%s requires exactly one connector' % route_type)
            lines.append('connector %s' % connectors[0])
        if route_type != 'DefaultRoute':
            if not filters:
                raise MissingKeyError('%s router requires filters' % route_type)
            lines.append('filters %s' % ';'.join(filters))

        self.run_session('mtrouter -a', lines)
        self.persist()
        return self.get_router(order)

    def simple_mtrouter_action(self, action, order, return_mtroute=True):
        self.run_action('mtrouter -%s %s' % (action, order))
        self.persist()
        if return_mtroute:
            return self.get_router(order)
        return {'order': order}

    def destroy(self, order):
        """Delete a mtrouter. One parameter required, the router identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent router
        - 400: other error
        """
        return self.simple_mtrouter_action('r', order, return_mtroute=False)
