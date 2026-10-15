from ..exceptions import DuplicateEntryError, MissingKeyError
from ..tools import table_rows
from .conn import TelnetConnection

import logging

logger = logging.getLogger(__name__)


class Groups(TelnetConnection):
    "Groups for managing *Jasmin* user groups (*not* Django auth groups)"
    lookup_field = 'gid'
    available_actions = ['list', 'add', 'delete', 'enable', 'disable']

    @staticmethod
    def parse_list(output):
        """Parse ``group -l`` output; a ``!`` prefix marks a disabled group."""
        groups = []
        for row in table_rows(output):
            gid = row.split()[0]
            groups.append({'name': gid.lstrip('!'), 'status': 'disabled' if gid.startswith('!') else 'enabled'})
        return groups

    def list(self):
        "List groups. No data parameters provided or required."
        return {'groups': self.parse_list(self.run_command('group -l'))}

    def create(self, data):
        """Create a group.
        One POST parameter required, the group identifier (a string)
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: gid
          description: Group identifier
          required: true
          type: string
          paramType: form
        """
        gid = (data.get('gid') or '').strip()
        if not gid:
            raise MissingKeyError('Missing gid (group identifier)')
        # jcli silently replaces an existing group instead of refusing the duplicate.
        if any(g['name'] == gid for g in self.list()['groups']):
            raise DuplicateEntryError('Group %s already exists' % gid)
        self.run_session('group -a', ['gid %s' % gid])
        self.persist()
        return {'name': gid}

    def simple_group_action(self, action, gid):
        self.run_action('group -%s %s' % (action, gid))
        self.persist()
        return {'name': gid}

    def destroy(self, gid):
        """Delete a group. One parameter required, the group identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent group
        - 400: other error
        """
        return self.simple_group_action('r', gid)

    def enable(self, gid):
        """Enable a group. One parameter required, the group identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent group
        - 400: other error
        """
        return self.simple_group_action('e', gid)

    def disable(self, gid):
        """Disable a group.

        One parameter required, the group identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent group
        - 400: other error
        """
        return self.simple_group_action('d', gid)
