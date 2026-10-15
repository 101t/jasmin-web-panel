from main.core.tools import table_rows
from main.core.exceptions import DuplicateEntryError, MissingKeyError, ObjectNotFoundError
from .conn import TelnetConnection

import logging

logger = logging.getLogger(__name__)


class HTTPCCM(TelnetConnection):
    "HTTPCCM for managing HTTP Client Connectors"
    lookup_field = 'cid'
    available_actions = ['list', 'add', 'delete', 'enable', 'disable']

    @staticmethod
    def parse_list(output):
        """Parse ``httpccm -l`` rows: cid, type, method, url."""
        connectors = []
        for row in table_rows(output):
            fields = row.split(None, 3)
            if len(fields) == 4:
                cid, ctype, method, url = fields
                connectors.append({'cid': cid, 'type': ctype, 'method': method, 'url': url.strip()})
        return connectors

    @staticmethod
    def parse_show(output):
        """Parse ``httpccm -s`` output, made of ``key = value`` lines."""
        httpccm = {}
        for line in output.split('\n'):
            key, sep, value = line.partition(' = ')
            if sep:
                httpccm[key.strip()] = value.strip()
        return httpccm

    def get_httpccm(self, cid, silent=False):
        output = self.run_command('httpccm -s %s' % cid)
        if output.startswith('Unknown') or output.startswith('Usage'):
            if silent:
                return
            raise ObjectNotFoundError('Unknown connector: %s' % cid)
        return self.parse_show(output)

    def get_connector_list(self):
        return self.parse_list(self.run_command('httpccm -l'))

    def simple_httpccm_action(self, action, cid):
        self.run_action('httpccm -%s %s' % (action, cid))
        self.persist()
        return {'name': cid}

    def list(self):
        """List HTTP Client Connectors. No parameters"""
        return {'connectors': self.get_connector_list()}

    def retrieve(self, cid):
        """Retreive data for one connector
        Required parameter: cid (connector id)"""
        connector = self.get_httpccm(cid, silent=False)
        list_data = next((c for c in self.get_connector_list() if c['cid'] == cid), None)
        if not list_data:
            raise ObjectNotFoundError('Unknown connector: %s' % cid)
        connector.update(list_data)
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
        keys = ('cid', 'url', 'method')
        values = {key: (data.get(key) or '').strip() for key in keys}
        missing = [key for key in keys if not values[key]]
        if missing:
            raise MissingKeyError('Missing parameter: %s' % ', '.join(missing))
        if any(c['cid'] == values['cid'] for c in self.get_connector_list()):
            raise DuplicateEntryError('HTTP connector %s already exists' % values['cid'])
        self.run_session('httpccm -a', ['%s %s' % (key, values[key]) for key in keys])
        self.persist()
        return {'cid': values['cid']}

    def destroy(self, cid):
        """Delete an http connector.
        One parameter required, the connector identifier

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent group
        - 400: other error
        """
        return self.simple_httpccm_action('r', cid)
