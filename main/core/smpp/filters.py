import logging
from collections import OrderedDict

from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError

from main.core.exceptions import (
    JasminError,
    UnknownError, MissingKeyError,
    ObjectNotFoundError
)
from main.core.tools import set_ikeys, split_cols
from .conn import TelnetConnection

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)


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

    def _list(self):
        "List Filters as python dict"
        self.telnet.sendline('filter -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        if len(result) < 3:
            return {'filters': []}
        results = [l.replace(', ', ',').replace('(!)', '')
                   for l in result[2:-2] if l]
        filters = split_cols(results)
        return {
            'filters':
                [
                    {
                        'fid': f[0].strip().lstrip('#'),
                        'type': f[1],
                        'routes': f[2] + ' ' + f[3],
                        'description': ' '.join(f[4:])
                    } for f in filters
                ]
        }

    def list(self):
        "List Filters. No parameters"
        return self._list()

    def get_filter(self, fid):
        "Return data for one filter as Python dict"
        filters = self._list()['filters']
        try:
            return {'filter':
                        next((m for m in filters if m['fid'] == fid), None)
                    }
        except StopIteration:
            raise ObjectNotFoundError('No Filter with fid: %s' % fid)

    def retrieve(self, fid):
        "Details for one Filter by fid (integer)"
        return self.get_filter(fid)

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
        try:
            ftype, fid = data['type'], data['fid']
        except IndexError:
            raise MissingKeyError('Missing parameter: type or fid required')
        ftype = ftype.lower()
        self.telnet.sendline('filter -a')
        self.telnet.expect(r'Adding a new Filter(.+)\n' + INTERACTIVE_PROMPT)
        ikeys = OrderedDict({'type': ftype, 'fid': fid})
        if ftype != 'transparentfilter':
            try:
                parameter = data['parameter']
            except MultiValueDictKeyError:
                raise MissingKeyError('%s filter requires parameter' % ftype)
            if ftype == 'connectorfilter':
                ikeys['cid'] = parameter
            elif ftype == 'userfilter':
                ikeys['uid'] = parameter
            elif ftype == 'groupfilter':
                ikeys['gid'] = parameter
            elif ftype == 'sourceaddrfilter':
                ikeys['source_addr'] = parameter
            elif ftype == 'destinationaddrfilter':
                ikeys['destination_addr'] = parameter
            elif ftype == 'shortmessagefilter':
                ikeys['short_message'] = parameter
            elif ftype == 'dateintervalfilter':
                ikeys['dateInterval'] = parameter
            elif ftype == 'timeintervalfilter':
                ikeys['timeInterval'] = parameter
            elif ftype == 'tagfilter':
                ikeys['tag'] = parameter
            elif ftype == 'evalpyfilter':
                ikeys['pyCode'] = parameter
        set_ikeys(self.telnet, ikeys)
        self.telnet.sendline('persist')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'filter': self.get_filter(fid)}

    def simple_filter_action(self, action, fid, return_filter=True):
        self.telnet.sendline('filter -%s %s' % (action, fid))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown Filter: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist')
            if return_filter:
                self.telnet.expect(r'.*' + STANDARD_PROMPT)
                return {'filter': self.get_filter(fid)}
            else:
                return {'fid': fid}
        elif matched_index == 1:
            raise UnknownError(detail='No filter:' + fid)
        else:
            raise JasminError(self.telnet.match.group(1))

    def destroy(self, fid):
        """Delete a filter. One parameter required, the filter identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent filter
        - 400: other error
        """
        return self.simple_filter_action('r', fid, return_filter=False)
