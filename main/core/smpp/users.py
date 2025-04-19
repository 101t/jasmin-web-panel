from django.conf import settings

from main.core.tools import set_ikeys
from main.core.exceptions import (JasminSyntaxError, JasminError,
                        UnknownError, MissingKeyError,
                        ObjectNotFoundError)
from .conn import TelnetConnection

import logging

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)

class Users(TelnetConnection):
    "Users for managing *Jasmin* users (*not* Django auth users)"
    lookup_field = 'uid'
    
    def get_user(self, uid, silent=False):
        """Gets a single users data
        silent supresses Http404 exception if user not found"""
        self.telnet.sendline('user -s %s' % uid)
        matched_index = self.telnet.expect([
                r'.+Unknown User:.*' + STANDARD_PROMPT,
                r'.+Usage: user.*' + STANDARD_PROMPT,
                r'(.+)\n' + STANDARD_PROMPT,
        ])
        if matched_index != 2:
            if silent:
                return
            else:
                raise ObjectNotFoundError('Unknown user: %s' % uid)
        result = self.telnet.match.group(1)
        user = {}
        for line in [l for l in result.splitlines() if l][1:]:
            d = [str(x, 'utf-8') for x in line.split() if x]
            if len(d) == 2:
                user[d[0]] = d[1]
            elif len(d) == 4:
                #Not DRY, could be more elegant
                if not d[0] in user:
                    user[d[0]] = {}
                if not d[1] in user[d[0]]:
                    user[d[0]][d[1]] = {}
                if not d[2] in user[d[0]][d[1]]:
                    user[d[0]][d[1]][d[2]] = {}
                user[d[0]][d[1]][d[2]] = d[3]
            #each line has two or four lines so above exhaustive
        return user

    def retrieve(self, uid):
        "Retrieve data for one user"
        return {'user': self.get_user(uid)}

    def list(self):
        "List users. No parameters"
        self.telnet.sendline('user -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = self.telnet.match.group(0).strip()
        if len(result) < 3:
            return {'users': []}

        results = [l for l in result.splitlines() if l]
        annotated_uids = [str(u.split(None, 1)[0][1:], 'utf-8') for u in results[2:-2]]
        users = []
        for auid in annotated_uids:
            if auid[0] == '!':
                udata = self.get_user(auid[1:], True)
                udata['status'] = 'disabled'
            else:
                udata = self.get_user(auid, True)
                udata['status'] = 'enabled'
            users.append(udata)
        return {
                #return users skipping None (== nonexistent user)
                'users': [u for u in users if u]
            }

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
        try:
            uid, gid, username, password = \
                data['uid'], data['gid'], data['username'], data['password']
        except Exception:
            raise MissingKeyError('Missing parameter: uid, gid, username and/or password required')
        self.telnet.sendline('user -a')
        self.telnet.expect(r'Adding a new User(.+)\n' + INTERACTIVE_PROMPT)
        set_ikeys(
            self.telnet,
            {
                'uid': uid, 'gid': gid, 'username': username,
                'password': password
            }
        )
        self.telnet.sendline('persist\n')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'user': self.get_user(uid)}

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
        self.telnet.sendline('user -u ' + uid)
        matched_index = self.telnet.expect([
            r'.*Updating User(.*)' + INTERACTIVE_PROMPT,
            r'.*Unknown User: (.*)' + STANDARD_PROMPT,
            r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
        ])
        if matched_index == 1:
            raise UnknownError(detail='Unknown user:' + uid)
        if matched_index != 0:
            raise JasminError(detail=" ".join(self.telnet.match.group(0).split()))
        updates = data
        if not ((type(updates) is list) and (len(updates) >= 1)):
            raise JasminSyntaxError('updates should be a list')
        for update in updates:
            if not ((type(update) is list) and (len(update) >= 1)):
                raise JasminSyntaxError("Not a list: %s" % update)
            self.telnet.sendline(" ".join([x for x in update]))
            matched_index = self.telnet.expect([
                r'.*(Unknown User key:.*)' + INTERACTIVE_PROMPT,
                r'.*(Error:.*)' + STANDARD_PROMPT,
                r'.*' + INTERACTIVE_PROMPT,
                r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
            ])
            if matched_index != 2:
                raise JasminSyntaxError(
                    detail=" ".join(self.telnet.match.group(1).split()))
        self.telnet.sendline('ok')
        ok_index = self.telnet.expect([
            r'(.*)' + INTERACTIVE_PROMPT,
            r'.*' + STANDARD_PROMPT,
        ])
        if ok_index == 0:
            raise JasminSyntaxError(
                detail=" ".join(self.telnet.match.group(1).split()))
        self.telnet.sendline('persist\n')
        #Not sure why this needs to be repeated
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'user': self.get_user(uid)}

    def simple_user_action(self, action, uid, return_user=True):
        self.telnet.sendline('user -%s %s' % (action, uid))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown User: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist\n')
            if return_user:
                self.telnet.expect(r'.*' + STANDARD_PROMPT)
                return {'user': self.get_user(uid)}
            else:
                return {'uid': uid}
        elif matched_index == 1:
            raise UnknownError(detail='No user:' +  uid)
        else:
            raise JasminError(self.telnet.match.group(1))

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
