from django.conf import settings

from main.core.tools import set_ikeys, split_cols
from main.core.exceptions import (
    JasminSyntaxError, JasminError, ActionFailed,
    ObjectNotFoundError, UnknownError, 
)
from .conn import TelnetConnection

import logging

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)

class HTTPCCM(TelnetConnection):
    "HTTPCCM for managing HTTP Client Connectors"
    lookup_field = 'cid'
    available_actions = ['list', 'add', 'delete', 'enable', 'disable']
    
    def get_httpccm(self, cid, silent=False):
        #Some of this could be abstracted out - similar pattern in users.py
        self.telnet.sendline('httpccm -s ' + cid)
        matched_index = self.telnet.expect([
                r'.+Unknown connector:.*' + STANDARD_PROMPT,
                r'.+Usage:.*' + STANDARD_PROMPT,
                r'(.+)\n' + STANDARD_PROMPT,
        ])
        if matched_index != 2:
            if silent:
                return
            else:
                raise ObjectNotFoundError('Unknown connector: %s' % cid)
        result = self.telnet.match.group(1)
        httpccm = {}
        for line in result.splitlines():
            d = [x for x in line.split() if x]
            if len(d) == 2:
                httpccm[d[0]] = d[1]
        return httpccm

    def get_connector_list(self):
        self.telnet.sendline('httpccm -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        if len(result) < 3:
            return []
        return split_cols(result[2:-2])

    def simple_httpccm_action(self, action, cid):
        self.telnet.sendline('httpccm -%s %s' % (action, cid))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown connector: (.+)' + STANDARD_PROMPT,
            r'(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist')
            return {'name': cid}
        elif matched_index == 1:
            raise ObjectNotFoundError('Unknown HTTP Connector: %s' % cid)
        else:
            raise ActionFailed(self.telnet.match.group(1))

    def list(self):
        """List HTTP Client Connectors. No parameters
        Differs from slightly from telent CLI names and values:

        1. the "service" column is called "status"
        2. the cid is the full connector id of the form https(cid)
        """
        connector_list = self.get_connector_list()
        connectors = []
        for raw_data in connector_list:
            if raw_data[0][0] == '#':
                cid = raw_data[0][1:]
                connector = self.get_httpccm(cid, True)
                connector.update(
                    cid=cid,
                    type=raw_data[1],
                    method=raw_data[2],
                    url=raw_data[3]
                )
                connectors.append(connector)
        return {'connectors': connectors}

    def retrieve(self, cid):
        """Retreive data for one connector
        Required parameter: cid (connector id)"""
        connector = self.get_httpccm(cid, silent=False)
        connector_list = self.get_connector_list()
        list_data = next(
            (raw_data for raw_data in connector_list if
                raw_data[0] == '#' + cid),
            None
        )
        if not list_data:
            raise ObjectNotFoundError('Unknown connector: %s' % cid)
        connector.update(
                    cid=cid,
                    type=list_data[1],
                    method=list_data[2],
                    url=list_data[3]
                )
        return {'connector': connector}

    def create(self, data):
        """Create an HTTP Client Connector.
        Required parameter: cid (connector id)
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: cid
          description: Connector identifier
          required: true
          type: string
          paramType: form
        - name: url
          description: URL to be called with message parameters
          required: true
          type: string
          paramType: form
        - name: method
          description: Calling method (GET or POST)
          required: true
          type: string
          paramType: form
        """
        self.telnet.sendline('httpccm -a')

        for k, v in data.items():
            self.telnet.sendline("%s %s" % (k, v))
        self.telnet.sendline('ok')
        matched_index = self.telnet.expect([
            r'.*(HttpConnector url syntax is invalid.*)' + INTERACTIVE_PROMPT,
            r'.*(HttpConnector method syntax is invalid, must be GET or POST.*)' + INTERACTIVE_PROMPT,
            r'.*' + INTERACTIVE_PROMPT,
            r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
        ])
        if matched_index != 2:
            raise JasminSyntaxError(
                detail=" ".join(self.telnet.match.group(1).split()))
        self.telnet.sendline('persist\n')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'cid': data['cid']}

    def destroy(self, cid):
        """Delete an http connector.
        One parameter required, the connector identifier

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent group
        - 400: other error
        """
        return self.simple_httpccm_action('r', cid)

