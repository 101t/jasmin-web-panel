from django.conf import settings

from ..exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError

from .conn import TelnetConnection
import logging

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)

class Groups(TelnetConnection):
    "Groups for managing *Jasmin* user groups (*not* Django auth groups)"
    lookup_field = 'gid'
    available_actions = ['list', 'add', 'delete', 'enable', 'disable']

    def list(self):
        "List groups. No data parameters provided or required."
        self.telnet.sendline('group -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        if len(result) < 3:
            return {'groups': []}
        groups = result[2:-2]
        return {
            'groups':
            [
                {
                    'name': g.strip().lstrip('!#'), 'status': (
                        'disabled' if g[1] == '!' else 'enabled'
                    )
                } for g in groups
            ]
        }

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
        self.telnet.sendline('group -a')
        self.telnet.expect(r'Adding a new Group(.+)\n' + INTERACTIVE_PROMPT)
        if not 'gid' in data:
            logger.error("MissingKeyError: {}".format(MissingKeyError('Missing gid (group identifier)')))
            #raise MissingKeyError('Missing gid (group identifier)')
        self.telnet.sendline('gid ' + data['gid'] + '\n')
        self.telnet.expect(INTERACTIVE_PROMPT)
        self.telnet.sendline('ok\n')

        matched_index = self.telnet.expect([
            r'.+Successfully added(.+)\[(.+)\][\n\r]+' + STANDARD_PROMPT,
            r'.+Error: (.+)[\n\r]+' + INTERACTIVE_PROMPT,
            r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
        ])
        if matched_index == 0:
            gid = self.telnet.match.group(2).strip()
            self.telnet.sendline('persist')
            return {'name': gid}
        else:
            logger.error("ActionFailed: {}".format(ActionFailed(self.telnet.match.group(1))))
            #raise ActionFailed(self.telnet.match.group(1))

    def simple_group_action(self, action, gid):
        self.telnet.sendline('group -%s %s' % (action, gid))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown Group: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist')
            return {'name': gid}
        elif matched_index == 1:
            logger.error("ObjectNotFoundError: {}".format(ObjectNotFoundError('Unknown group: %s' % gid)))
            #raise ObjectNotFoundError('Unknown group: %s' % gid)
        else:
            logger.error("ActionFailed: {}".format(ActionFailed(self.telnet.match.group(1))))
            #raise ActionFailed(self.telnet.match.group(1))

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
