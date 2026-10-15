import logging
from typing import List

from main.core.exceptions import (
    DuplicateEntryError,
    MissingKeyError,
    MultipleValuesRequiredKeyError,
    ObjectNotFoundError,
)
from main.core.utils import is_int
from main.core.tools import as_list, parse_route_row, table_rows

from .conn import TelnetConnection

logger = logging.getLogger(__name__)


class MORouter(TelnetConnection):
    """MORouter for managing MO Routes"""
    lookup_field = 'order'
    available_actions = ['list', 'add', 'delete']

    MO_ROUTER_TYPES = (
        ('DefaultRoute', 'Default Route'),
        ('StaticMORoute', 'Static MO Route'),
        ('RandomRoundrobinMORoute', 'Random Roundrobin MO Route'),
        ('FailoverMORoute', 'Failover MO Route'),
    )

    @staticmethod
    def parse_list(output) -> List[dict]:
        """Parse ``morouter -l`` output as a list of dicts"""
        routes = []
        for row in table_rows(output):
            route = parse_route_row(row, rated=False)
            if route is None:
                logger.warning('Unexpected MO route row: %r', row)
            else:
                routes.append(route)
        return routes

    def _list(self) -> List[dict]:
        """List MO router as python dict"""
        return self.parse_list(self.run_command('morouter -l'))

    def list(self):
        """List MO routers. No parameters"""
        return {'morouters': self._list()}

    def get_router(self, order: str):
        """Return data for one morouter as Python dict"""
        try:
            return {'morouter': next(m for m in self._list() if m['order'] == str(order))}
        except StopIteration:
            raise ObjectNotFoundError('No MoROuter with order: %s' % order)

    def router_exists(self, order: str) -> bool:
        return any(m['order'] == str(order) for m in self._list())

    def retrieve(self, order):
        """Details for one MORouter by order (integer)"""
        return self.get_router(order)

    def flush(self):
        """Flush entire routing table"""
        self.run_action('morouter -f')
        self.persist()
        return {'morouters': []}

    def create(self, data):
        """Add a new MORouter

        ``smppconnectors`` are SMPP server usernames (system_id) delivered as ``smpps(username)``;
        ``httpconnectors`` are HTTP connector ids delivered as ``http(cid)``. Both, and
        ``filters``, accept a list or a comma-separated string.
        """
        route_type = data.get('type') or "DefaultRoute"
        # Jasmin always stores the DefaultRoute at order 0.
        order = "0" if route_type == 'DefaultRoute' else str(data.get('order') or '').strip()
        if not is_int(order) or int(order) < 0:
            raise MissingKeyError('Order must be a positive integer')
        filters = as_list(data.get('filters'))
        connectors = ['smpps(%s)' % c for c in as_list(data.get('smppconnectors'))] + \
                     ['http(%s)' % c for c in as_list(data.get('httpconnectors'))]

        if self.router_exists(order):
            raise DuplicateEntryError('Order %s already exists' % order)

        lines = ['type %s' % route_type, 'order %s' % order]
        if route_type in ('RandomRoundrobinMORoute', 'FailoverMORoute'):
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

        self.run_session('morouter -a', lines)
        self.persist()
        return self.get_router(order)

    def simple_morouter_action(self, action, order, return_moroute=True):
        self.run_action('morouter -%s %s' % (action, order))
        self.persist()
        if return_moroute:
            return self.get_router(order)
        return {'order': order}

    def destroy(self, order):
        """Delete a morouter. One parameter required, the router identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent router
        - 400: other error
        """
        return self.simple_morouter_action('r', order, return_moroute=False)
