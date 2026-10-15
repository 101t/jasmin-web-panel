from main.core.tools import table_rows
from main.core.exceptions import DuplicateEntryError, JasminSyntaxError, MissingKeyError, ObjectNotFoundError
from .conn import TelnetConnection

import logging
import re

logger = logging.getLogger(__name__)

CREDENTIAL_KEYS = ('mt_messaging_cred', 'smpps_cred')
USER_ROW_RE = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+\(!\))?\s+(\S+)(?:\s+\(!\))?\s+(\S+)$')


class Users(TelnetConnection):
    "Users for managing *Jasmin* users (*not* Django auth users)"
    lookup_field = 'uid'

    @staticmethod
    def parse_user(output):
        """Parse ``user -s`` output into a dict.

        Plain keys are ``key value`` lines; credentials are ``cred section key value`` lines, and
        their value may contain spaces (regex filters, "Unknown (object is from an old ...)").
        """
        user = {}
        for line in output.split('\n'):
            fields = line.split(None, 1)
            if not fields:
                continue
            if fields[0] in CREDENTIAL_KEYS:
                cred = line.split(None, 3)
                if len(cred) < 3:
                    continue
                user.setdefault(cred[0], {}).setdefault(cred[1], {})[cred[2]] = cred[3] if len(cred) == 4 else ''
            else:
                user[fields[0]] = fields[1] if len(fields) == 2 else ''
        return user

    @staticmethod
    def parse_list(output):
        """Parse ``user -l`` output into ``(uid, enabled)`` pairs; ``!`` marks a disabled user."""
        return [(row.split()[0].lstrip('!'), not row.startswith('!')) for row in table_rows(output)]

    @staticmethod
    def parse_summary(output):
        """Parse ``user -l`` rows (one jcli command for all users, no per-user lookups).

        Rows look like ``u1  !g1  bob  100.0  ND (!)  ND/ND``: uid, gid, username, balance,
        SMS count and HTTP/SMPP throughput; ``!`` marks a disabled user or group and ``(!)``
        flags a user without any quota.
        """
        users = []
        for row in table_rows(output):
            match = USER_ROW_RE.match(row.strip())
            fields = match.groups() if match else row.split()[:3]
            if len(fields) < 3:
                continue
            user = {
                'uid': fields[0].lstrip('!'),
                'gid': fields[1].lstrip('!'),
                'username': fields[2],
                'status': 'disabled' if fields[0].startswith('!') else 'enabled',
            }
            if match:
                user.update(balance=fields[3], sms_count=fields[4], throughput=fields[5])
            users.append(user)
        return users

    def list_summary(self):
        "List users with one jcli command (no credentials), for pickers and dropdowns"
        return {'users': self.parse_summary(self.run_command('user -l'))}

    def get_user(self, uid, silent=False):
        """Gets a single users data
        silent supresses Http404 exception if user not found"""
        output = self.run_command('user -s %s' % uid)
        if output.startswith('Unknown User') or output.startswith('Usage'):
            if silent:
                return None
            raise ObjectNotFoundError('Unknown user: %s' % uid)
        return self.parse_user(output)

    def retrieve(self, uid):
        "Retrieve data for one user"
        return {'user': self.get_user(uid)}

    def list(self):
        "List users. No parameters"
        users = []
        for uid, enabled in self.parse_list(self.run_command('user -l')):
            user = self.get_user(uid, silent=True)
            if user:
                user['status'] = 'enabled' if enabled else 'disabled'
                users.append(user)
        return {'users': users}

    def create(self, data):
        """Create a User.
        Required parameters: username, password, uid (user identifier), gid (group identifier),
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: uid
          description: Username identifier
          required: true
          type: string
          paramType: form
        - name: gid
          description: Group identifier
          required: true
          type: string
          paramType: form
        - name: username
          description: Username
          required: true
          type: string
          paramType: form
        - name: password
          description: Password
          required: true
          type: string
          paramType: form
        """
        keys = ('uid', 'gid', 'username', 'password')
        values = {key: (data.get(key) or '').strip() for key in keys}
        missing = [key for key in keys if not values[key]]
        if missing:
            raise MissingKeyError('Missing parameter: %s' % ', '.join(missing))
        # jcli silently replaces an existing user, resetting its quotas and authorizations.
        if self.get_user(values['uid'], silent=True) is not None:
            raise DuplicateEntryError('User %s already exists' % values['uid'])
        self.run_session('user -a', ['%s %s' % (key, values[key]) for key in keys])
        self.persist()
        return {'user': self.get_user(values['uid'])}

    def partial_update(self, data, uid):
        """Update some user attributes

        JSON parameters only. The updates parameter is a list of lists.
        Each list is a list of valid arguments to user update. For example:

        * ["gid", "mygroup"] will set the user's group to mygroup
        * ["mt_messaging_cred", "authorization", "smpps_send", "False"]
        will remove the user privilege to send SMSs through the SMPP API.
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
        updates = data
        if not (isinstance(updates, (list, tuple)) and updates):
            raise JasminSyntaxError('updates should be a list')
        lines = []
        for update in updates:
            if not (isinstance(update, (list, tuple)) and update):
                raise JasminSyntaxError("Not a list: %s" % (update,))
            lines.append(" ".join(str(x) for x in update))
        self.run_session('user -u %s' % uid, lines)
        self.persist()
        return {'user': self.get_user(uid)}

    def simple_user_action(self, action, uid, return_user=True):
        self.run_action('user -%s %s' % (action, uid))
        self.persist()
        if return_user:
            return {'user': self.get_user(uid)}
        return {'uid': uid}

    def destroy(self, uid):
        """Delete a user. One parameter required, the user identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent user
        - 400: other error
        """
        return self.simple_user_action('r', uid, return_user=False)

    def enable(self, uid):
        """Enable a user. One parameter required, the user identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent user
        - 400: other error
        """
        return self.simple_user_action('e', uid)

    def disable(self, uid):
        """Disable a user.

        One parameter required, the user identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent user
        - 400: other error
        """
        return self.simple_user_action('d', uid)

    def smpp_unbind(self, uid):
        """Unbind user from smpp server

        One parameter required, the user identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful unbind
        - 404: nonexistent user
        - 400: other error
        """
        return self.simple_user_action('-smpp-unbind', uid)

    def smpp_ban(self, uid):
        """Unbind and ban user from smpp server

        One parameter required, the user identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful ban and unbind
        - 404: nonexistent user
        - 400: other error
        """
        return self.simple_user_action('-smpp-ban', uid)
