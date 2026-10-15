from main.core.tools import table_rows
from main.core.exceptions import DuplicateEntryError, JasminSyntaxError, MissingKeyError, ObjectNotFoundError
from .conn import TelnetConnection

import logging

logger = logging.getLogger(__name__)

# The connector id and the runtime fields that ``list()`` adds; jcli cannot update them.
READ_ONLY_KEYS = ('cid', 'status', 'session', 'starts', 'stops')


class SMPPCCM(TelnetConnection):
    "SMPPCCM for managing SMPP Client Connectors"
    lookup_field = 'cid'

    @staticmethod
    def parse_show(output):
        """Parse ``smppccm -s`` output; values may be empty (``systype``) or contain spaces."""
        smppccm = {}
        for line in output.split('\n'):
            fields = line.split(None, 1)
            if fields:
                smppccm[fields[0]] = fields[1].strip() if len(fields) == 2 else ''
        return smppccm

    @staticmethod
    def parse_list(output):
        """Parse ``smppccm -l`` rows: cid, service status, session state, starts, stops."""
        connectors = []
        for row in table_rows(output):
            fields = row.split()
            if len(fields) >= 5:
                connectors.append({
                    'cid': fields[0], 'status': fields[1], 'session': fields[2],
                    'starts': fields[3], 'stops': fields[4],
                })
        return connectors

    def get_smppccm(self, cid, silent=False):
        output = self.run_command('smppccm -s %s' % cid)
        if output.startswith('Unknown connector') or output.startswith('Usage'):
            if silent:
                return
            raise ObjectNotFoundError('Unknown connector: %s' % cid)
        return self.parse_show(output)

    def get_connector_list(self):
        return self.parse_list(self.run_command('smppccm -l'))

    def simple_smppccm_action(self, action, cid):
        self.run_action('smppccm -%s %s' % (action, cid))
        self.persist()
        return {'name': cid}

    def list(self):
        """List SMPP Client Connectors. No parameters
        Differs from slightly from telent CLI names and values:

        1. the "service" column is called "status"
        2. the cid is the full connector id of the form smpps(cid)
        """
        connectors = []
        for list_data in self.get_connector_list():
            connector = self.get_smppccm(list_data['cid'], True) or {}
            connector.update(list_data)
            connectors.append(connector)
        return {'connectors': connectors}

    def retrieve(self, cid):
        """Retreive data for one connector
        Required parameter: cid (connector id)"""
        connector = self.get_smppccm(cid, silent=False)
        list_data = next((c for c in self.get_connector_list() if c['cid'] == cid), None)
        if not list_data:
            raise ObjectNotFoundError('Unknown connector: %s' % cid)
        connector.update(list_data)
        return {'connector': connector}

    @staticmethod
    def _lines(data, skip=()):
        """jcli ``key value`` lines for the keys that carry a value."""
        if not isinstance(data, dict):
            raise JasminSyntaxError('updates should be a a key value array')
        return ['%s %s' % (k, str(v).strip()) for k, v in data.items()
                if k not in skip and v is not None and str(v).strip() != '']

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
        cid = (data.get('cid') or '').strip() if isinstance(data, dict) else ''
        if not cid:
            raise MissingKeyError('Missing parameter: cid')
        if any(c['cid'] == cid for c in self.get_connector_list()):
            raise DuplicateEntryError('SMPP connector %s already exists' % cid)
        self.run_session('smppccm -a', ['cid %s' % cid] + self._lines(data, skip=READ_ONLY_KEYS))
        self.persist()
        return {'cid': cid}

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

        JSON parameters only. The updates parameter is a key value array. Only keys whose value
        differs from the running configuration are sent: re-sending host, port, username,
        password or systype would make Jasmin restart the connector for nothing.
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
        current = self.get_smppccm(cid, silent=False)
        changed = {k: v for k, v in data.items() if str(current.get(k, '')).strip() != str(v).strip()} \
            if isinstance(data, dict) else data
        lines = self._lines(changed, skip=READ_ONLY_KEYS)
        if lines:
            self.run_session('smppccm -u %s' % cid, lines)
            self.persist()
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
