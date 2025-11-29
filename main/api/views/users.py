from django.conf import settings

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT


class UsersViewSet(ViewSet):
    """
    UsersViewSet to manage Jasmin users.
    
    Jasmin users are separate from Django authentication users.
    Each user belongs to a group and has credentials for sending SMS.
    """
    lookup_field = 'uid'

    def list(self, request):
        """
        List all Jasmin users.
        
        Returns a list of all users with their status (enabled/disabled).
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/users/
        ```
        
        **Example Response:**
        ```json
        {
            "users": [
                {"uid": "user1", "status": "enabled"},
                {"uid": "user2", "status": "disabled"}
            ]
        }
        ```
        """
        if not hasattr(request, 'telnet'):
            return Response(data={"status": "bad request"}, status=http_status.HTTP_400_BAD_REQUEST)
        telnet = request.telnet
        telnet.sendline('user -l')
        telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = telnet.match.group(0).strip().replace("\r", '').split("\n")
        if len(result) < 3:
            return Response(data={"users": []}, status=http_status.HTTP_200_OK)
        users = result[2:-2]
        return Response(data={"users": [
            {
                'uid': u.split()[0].strip().lstrip('!#'),
                'status': ('disabled' if '!' in u.split()[0] else 'enabled')
            } for u in users if u
        ]})

    def create(self, request):
        """
        Create a new Jasmin user.
        
        **Required Fields:**
        - `uid` - Unique user identifier
        - `gid` - Group identifier (must exist)
        - `username` - Username for authentication
        - `password` - Password for authentication
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"uid": "user1", "gid": "group1", "username": "user1", "password": "secret123"}' \\
          http://localhost:8000/api/users/
        ```
        
        **Example Response:**
        ```json
        {"uid": "user1"}
        ```
        """
        telnet = request.telnet
        required_fields = ['uid', 'gid', 'username', 'password']
        for field in required_fields:
            if field not in request.data:
                raise MissingKeyError(f'Missing {field}')
        
        telnet.sendline('user -a')
        telnet.expect(r'Adding a new User(.+)\n' + INTERACTIVE_PROMPT)
        
        for field in required_fields:
            telnet.sendline(f'{field} {request.data[field]}')
            telnet.expect(INTERACTIVE_PROMPT)
        
        telnet.sendline('ok\n')
        matched_index = telnet.expect([
            r'.+Successfully added(.+)\[(.+)\][\n\r]+' + STANDARD_PROMPT,
            r'.+Error: (.+)[\n\r]+' + INTERACTIVE_PROMPT,
            r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
        ])
        if matched_index == 0:
            uid = telnet.match.group(2).strip()
            telnet.sendline('persist\n')
            return Response(data={'uid': uid}, status=http_status.HTTP_201_CREATED)
        else:
            raise ActionFailed(telnet.match.group(1))

    def retrieve(self, request, uid):
        """
        Retrieve details of a single user.
        
        **URL Parameters:**
        - `uid` - User identifier
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/users/user1/
        ```
        
        **Example Response:**
        ```json
        {"uid": "user1"}
        ```
        """
        if not hasattr(request, 'telnet'):
            return Response(data={"status": "bad request"}, status=http_status.HTTP_400_BAD_REQUEST)
        telnet = request.telnet
        telnet.sendline(f'user -s {uid}')
        matched_index = telnet.expect([
            r'.+Unknown User:.*' + STANDARD_PROMPT,
            r'(.+)\n' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            raise ObjectNotFoundError(f'Unknown user: {uid}')
        return Response(data={'uid': uid})

    def destroy(self, request, uid):
        """
        Delete a user.
        
        **URL Parameters:**
        - `uid` - User identifier to delete
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/users/user1/
        ```
        
        **Example Response:**
        ```json
        {"uid": "user1"}
        ```
        """
        return self._simple_action(request.telnet, 'r', uid)

    @action(methods=['put'], detail=True)
    def enable(self, request, uid):
        """
        Enable a disabled user.
        
        **URL Parameters:**
        - `uid` - User identifier to enable
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/users/user1/enable/
        ```
        
        **Example Response:**
        ```json
        {"uid": "user1"}
        ```
        """
        return self._simple_action(request.telnet, 'e', uid)

    @action(methods=['put'], detail=True)
    def disable(self, request, uid):
        """
        Disable a user (prevents SMS sending).
        
        **URL Parameters:**
        - `uid` - User identifier to disable
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/users/user1/disable/
        ```
        
        **Example Response:**
        ```json
        {"uid": "user1"}
        ```
        """
        return self._simple_action(request.telnet, 'd', uid)

    def _simple_action(self, telnet, action, uid):
        telnet.sendline(f'user -{action} {uid}')
        matched_index = telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown User: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            telnet.sendline('persist\n')
            return Response(data={'uid': uid}, status=http_status.HTTP_200_OK)
        elif matched_index == 1:
            raise ObjectNotFoundError(f'Unknown user: {uid}')
        else:
            raise ActionFailed(telnet.match.group(1))


users_list = UsersViewSet.as_view({'get': 'list', 'post': 'create'})
users_detail = UsersViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
users_enable = UsersViewSet.as_view({'put': 'enable'})
users_disable = UsersViewSet.as_view({'put': 'disable'})
