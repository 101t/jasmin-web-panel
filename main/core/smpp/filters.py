import logging
import re

from main.core.exceptions import DuplicateEntryError, MissingKeyError, ObjectNotFoundError
from main.core.tools import table_rows
from .conn import TelnetConnection

logger = logging.getLogger(__name__)

# fid, type, the routes the filter applies to ("MO", "MT" or "MO MT"), then its description,
# e.g. "f1  UserFilter  MT  <U (uid=u1)>".
FILTER_ROW_RE = re.compile(r'^(\S+)\s+(\S+)\s+((?:MO|MT)(?:\s+(?:MO|MT))?)\s*(.*)$')


class Filters(TelnetConnection):
    "Filters Class"
    lookup_field = 'fid'
    available_actions = ['list', 'add', 'delete']

    FILTER_TYPES = (
        ('transparentfilter', 'Transparent Filter'),
        ('connectorfilter', 'Connector Filter'),
        ('userfilter', 'User Filter'),
        ('groupfilter', 'Group Filter'),
        ('sourceaddrfilter', 'Source Addr Filter'),
        ('destinationaddrfilter', 'Destination Addr Filter'),
        ('shortmessagefilter', 'Short Message Filter'),
        ('dateintervalfilter', 'Date Interval Filter'),
        ('timeintervalfilter', 'Time Interval Filter'),
        ('tagfilter', 'Tag Filter'),
        ('evalpyfilter', 'EvalPy Filter'),
    )
    FILTER_PARAMETERS = ['cid', 'uid', 'gid', 'source_addr', 'destination_addr', 'short_message', 'dateInterval', 'timeInterval', 'tag', 'pyCode']
    # The jcli key holding the single parameter of each filter type.
    PARAMETER_KEYS = {
        'connectorfilter': 'cid',
        'userfilter': 'uid',
        'groupfilter': 'gid',
        'sourceaddrfilter': 'source_addr',
        'destinationaddrfilter': 'destination_addr',
        'shortmessagefilter': 'short_message',
        'dateintervalfilter': 'dateInterval',
        'timeintervalfilter': 'timeInterval',
        'tagfilter': 'tag',
        'evalpyfilter': 'pyCode',
    }

    @staticmethod
    def parse_list(output):
        "Parse ``filter -l`` output as a list of dicts"
        filters = []
        for row in table_rows(output):
            match = FILTER_ROW_RE.match(row.strip())
            if not match:
                logger.warning('Unexpected filter row: %r', row)
                continue
            fid, ftype, routes, description = match.groups()
            filters.append({
                'fid': fid,
                'type': ftype,
                'routes': ' '.join(routes.split()),
                'description': description.strip(),
            })
        return filters

    def _list(self):
        "List Filters as python dict"
        return {'filters': self.parse_list(self.run_command('filter -l'))}

    def list(self):
        "List Filters. No parameters"
        return self._list()

    def get_filter(self, fid):
        "Return data for one filter as Python dict"
        for item in self._list()['filters']:
            if item['fid'] == fid:
                return item
        raise ObjectNotFoundError('No Filter with fid: %s' % fid)

    def retrieve(self, fid):
        "Details for one Filter by fid (integer)"
        return {'filter': self.get_filter(fid)}

    def create(self, data):
        """Create Filter.
        Required parameters: type, fid, parameters
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: type
          description: One of TransparentFilter, ConnectorFilter, UserFilter, GroupFilter, SourceAddrFilter, DestinationAddrFilter, ShortMessageFilter, DateIntervalFilter, TimeIntervalFilter, TagFilter, EvalPyFilter
          required: true
          type: string
          paramType: form
        - name: fid
          description: Filter id, used to identify filter
          required: true
          type: string
          paramType: form
        - name: parameter
          description: Parameter
          required: false
          type: string
          paramType: form
        """
        ftype = (data.get('type') or '').strip().lower()
        fid = (data.get('fid') or '').strip()
        if not ftype or not fid:
            raise MissingKeyError('Missing parameter: type or fid required')
        if ftype != 'transparentfilter' and ftype not in self.PARAMETER_KEYS:
            raise MissingKeyError('Unknown filter type: %s' % ftype)
        # jcli silently replaces an existing filter, even with another type.
        if any(f['fid'] == fid for f in self._list()['filters']):
            raise DuplicateEntryError('Filter %s already exists' % fid)
        lines = ['type %s' % ftype, 'fid %s' % fid]
        if ftype != 'transparentfilter':
            parameter = (data.get('parameter') or '').strip()
            if not parameter:
                raise MissingKeyError('%s filter requires parameter' % ftype)
            lines.append('%s %s' % (self.PARAMETER_KEYS[ftype], parameter))
        self.run_session('filter -a', lines)
        self.persist()
        return {'filter': self.get_filter(fid)}

    def simple_filter_action(self, action, fid, return_filter=True):
        self.run_action('filter -%s %s' % (action, fid))
        self.persist()
        if return_filter:
            return {'filter': self.get_filter(fid)}
        return {'fid': fid}

    def destroy(self, fid):
        """Delete a filter. One parameter required, the filter identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent filter
        - 400: other error
        """
        return self.simple_filter_action('r', fid, return_filter=False)
