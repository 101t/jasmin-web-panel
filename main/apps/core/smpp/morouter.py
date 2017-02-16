from collections import OrderedDict

from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError

from main.apps.core.tools import set_ikeys, split_cols
from main.apps.core.exceptions import (JasminSyntaxError, JasminError,
                        UnknownError, MissingKeyError,
                        MutipleValuesRequiredKeyError, ObjectNotFoundError)
from .conn import TelnetConnection

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT


class MORouter(object):
    "MORouter for managing MO Routes"
    lookup_field = 'order'
    def __init__(self, telnet):
        self.telnet = telnet
    def _list(self):
        "List MO router as python dict"
        self.telnet.sendline('morouter -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = self.telnet.match.group(0).strip().replace("\r", '').split("\n")
        if len(result) < 3:
            return {'morouters': []}
        results = [l.replace(', ', ',').replace('(!)', '')
            for l in result[2:-2] if l]
        routers = split_cols(results)
        print routers
        return {
            'morouters':
                [
                    {
                        'order': r[0].strip().lstrip('#'),
                        'type': r[1],
                        'connectors': [c.strip() for c in r[2].split(',')],
                        'filters': [c.strip() for c in ' '.join(r[3:]).split(',')
                            ] if len(r) > 3 else []
                    } for r in routers
                ]
        }

    def list(self):
        "List MO routers. No parameters"
        return self._list()

    def get_router(self, order):
        "Return data for one morouter as Python dict"
        morouters = self._list()['morouters']
        try:
            return {'morouter':
                next((m for m in morouters if m['order'] == order), None)
            }
        except StopIteration:
            raise ObjectNotFoundError('No MoROuter with order: %s' % order)

    def retrieve(self, order):
        "Details for one MORouter by order (integer)"
        return self.get_router(order)


    # methods=['delete']
    def flush(self):
        "Flush entire routing table"
        self.telnet.sendline('morouter -f')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        self.telnet.sendline('persist\n')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'morouters': []}

    def create(self, data):
        """Create MORouter.
        Required parameters: type, order, smppconnectors, httpconnectors
        More than one connector is allowed only for RandomRoundrobinMORoute
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: type
          description: One of DefaultRoute, StaticMORoute, RandomRoundrobinMORoute
          required: true
          type: string
          paramType: form
        - name: order
          description: Router order, also used to identify router
          required: true
          type: string
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
            rtype, order = data['type'], data['order']
        except IndexError:
            raise MissingKeyError(
                'Missing parameter: type or order required')
        rtype = rtype.lower()
        self.telnet.sendline('morouter -a')
        self.telnet.expect(r'Adding a new MO Route(.+)\n' + INTERACTIVE_PROMPT)
        ikeys = OrderedDict({'type': rtype})
        if rtype != 'defaultroute':
            try:
                filters = data['filters'].split(',')
            except MultiValueDictKeyError:
                raise MissingKeyError('%s router requires filters' % rtype)
            ikeys['filters'] = ';'.join(filters)
            ikeys['order'] = order
            print(ikeys)
        smppconnectors = data.get('smppconnectors', '')
        httpconnectors = data.get('httpconnectors', '')
        connectors = ['smpps(%s)' % c.strip()
                for c in smppconnectors.split(',') if c.strip()
            ] + ['http(%s)' % c for c in httpconnectors.split(',') if c.strip()]
        if rtype == 'randomroundrobinmoroute':
            if len(connectors) < 2:
                raise MutipleValuesRequiredKeyError(
                    'Round Robin route requires at least two connectors')
            ikeys['connectors'] = ';'.join(connectors)
        else:
            if len(connectors) != 1:
                raise MissingKeyError('one and only one connector required')
            ikeys['connector'] = connectors[0]
        set_ikeys(self.telnet, ikeys)
        self.telnet.sendline('persist\n')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'morouter': self.get_router(order)}

    def simple_morouter_action(self, action, order, return_moroute=True):
        self.telnet.sendline('morouter -%s %s' % (action, order))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown MO Route: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist\n')
            if return_moroute:
                self.telnet.expect(r'.*' + STANDARD_PROMPT)
                return {'morouter': self.get_router(fid)}
            else:
                return {'order': order}
        elif matched_index == 1:
            raise UnknownError(detail='No router:' +  order)
        else:
            raise JasminError(self.telnet.match.group(1))

    def destroy(self, order):
        """Delete a morouter. One parameter required, the router identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent router
        - 400: other error
        """
        return self.simple_morouter_action('r', order, return_moroute=False)
