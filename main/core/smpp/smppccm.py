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

class SMPPCCM(TelnetConnection):
    "SMPPCCM for managing SMPP Client Connectors"
    lookup_field = 'cid'

    def get_smppccm(self, cid, silent=False):
        #Some of this could be abstracted out - similar pattern in users.py
        self.telnet.sendline('smppccm -s ' + cid)
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
        smppccm = {}
        for line in result.splitlines():
            d = [x for x in line.split() if x]
            if len(d) == 2:
                smppccm[str(d[0], 'utf-8')] = str(d[1], 'utf-8')
        return smppccm

    def get_connector_list(self):
        self.telnet.sendline('smppccm -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        #print(self.telnet.match.group(0))
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        #print(result)
        if len(result) < 3:
            return []
        return split_cols(result[2:-2])

    def simple_smppccm_action(self, action, cid):
        self.telnet.sendline('smppccm -%s %s' % (action, cid))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown connector: (.+)' + STANDARD_PROMPT,
            r'(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist')
            return {'name': cid}
        elif matched_index == 1:
            logger.error("ObjectNotFoundError: {}".format(ObjectNotFoundError('Unknown SMPP Connector: %s' % cid)))
            #raise ObjectNotFoundError('Unknown SMPP Connector: %s' % cid)
        else:
            logger.error("ActionFailed: {}".format(ActionFailed(self.telnet.match.group(1))))
            #raise ActionFailed(self.telnet.match.group(1))
        return {}

    def list(self):
        """List SMPP Client Connectors. No parameters
        Differs from slightly from telent CLI names and values:

        1. the "service" column is called "status"
        2. the cid is the full connector id of the form smpps(cid)
        """
        connector_list = self.get_connector_list()
        connectors = []
        for raw_data in connector_list:
            if raw_data[0][0] == '#':
                cid = raw_data[0][1:]
                connector = self.get_smppccm(cid, True)
                connector.update(
                    cid=cid,
                    status=raw_data[1],
                    session=raw_data[2],
                    starts=raw_data[3],
                    stops=raw_data[4]
                )
                connectors.append(connector)
        return {'connectors': connectors}

    def retrieve(self, cid):
        """Retreive data for one connector
        Required parameter: cid (connector id)"""
        connector = self.get_smppccm(cid, silent=False)
        connector_list = self.get_connector_list()
        list_data = next(
            (raw_data for raw_data in connector_list if
                raw_data[0] == '#' + cid),
            None
        )
        connector.update(
            cid=cid,
            status=list_data[1],
            session=list_data[2],
            starts=list_data[3],
            stops=list_data[4]
        )
        return {'connector': connector}

    def create(self, data):
        """Create an SMPP Client Connector.
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
        """
        self.telnet.sendline('smppccm -a')
        updates = data
        for k, v in updates.items():
            if not ((type(updates) is dict) and (len(updates) >= 1)):
                raise JasminSyntaxError('updates should be a a key value array')
            self.telnet.sendline("%s %s" % (k, v))
            matched_index = self.telnet.expect([
                r'.*(Unknown SMPPClientConfig key:.*)' + INTERACTIVE_PROMPT,
                r'.*(Error:.*)' + STANDARD_PROMPT,
                r'.*' + INTERACTIVE_PROMPT,
                r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
            ])
            if matched_index != 2:
                raise JasminSyntaxError(
                    detail=" ".join(self.telnet.match.group(1).split()))
        self.telnet.sendline('ok')
        self.telnet.sendline('persist')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'cid': data['cid']}

    def destroy(self, cid):
        """Delete an smpp connector.
        One parameter required, the connector identifier

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent group
        - 400: other error
        """
        return self.simple_smppccm_action('r', cid)

    def partial_update(self, data, cid):
        """Update some SMPP connector attributes

        JSON parameters only. The updates parameter is a key value array
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: updates
          description: Items to update
          required: true
          type: array
          paramType: body
        """
        self.telnet.sendline('smppccm -u ' + cid)
        matched_index = self.telnet.expect([
            r'.*Updating connector(.*)' + INTERACTIVE_PROMPT,
            r'.*Unknown connector: (.*)' + STANDARD_PROMPT,
            r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
        ])
        if matched_index == 1:
            raise UnknownError(detail='Unknown connector:' + cid)
        if matched_index != 0:
            raise JasminError(detail=" ".join(self.telnet.match.group(0).split()))
        updates = data
        for k, v in updates.items():
            if not ((type(updates) is dict) and (len(updates) >= 1)):
                raise JasminSyntaxError('updates should be a a key value array')
            self.telnet.sendline("%s %s" % (k, v))
            matched_index = self.telnet.expect([
                r'.*(Unknown SMPPClientConfig key:.*)' + INTERACTIVE_PROMPT,
                r'.*(Error:.*)' + STANDARD_PROMPT,
                r'.*' + INTERACTIVE_PROMPT,
                r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
            ])
            if matched_index != 2:
                raise JasminSyntaxError(
                    detail=" ".join(self.telnet.match.group(1).split()))
        self.telnet.sendline('ok')
        ok_index = self.telnet.expect([
            r'.*(Error:.*)' + STANDARD_PROMPT,
            r'(.*)' + INTERACTIVE_PROMPT,
            r'.*' + STANDARD_PROMPT,
        ])
        if ok_index == 0:
            raise JasminSyntaxError(
                detail=" ".join(self.telnet.match.group(1).split()))
        self.telnet.sendline('persist')
        #Not sure why this needs to be repeated, just as with user
        self.telnet.expect(r'.*' + STANDARD_PROMPT)

        return {'connector': self.get_smppccm(cid, silent=False)}

    def start(self, cid):
        """Start SMPP Connector

        One parameter required, the connector identifier

        HTTP codes indicate result as follows

        - 200: successful start
        - 404: nonexistent connector
        - 400: other error - this includes failure to start because it is started.
        """
        return self.simple_smppccm_action('1', cid)

    def stop(self, cid):
        """Stop SMPP Connector

        One parameter required, the connector identifier

        HTTP codes indicate result as follows

        - 200: successful start
        - 404: nonexistent connector
        - 400: other error - this includes failure to stop because it is stopped.
        """
        return self.simple_smppccm_action('0', cid)
