from django.conf import settings

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT


class GroupsViewSet(ViewSet):
    """
    GroupsViewSet to manage Jasmin user groups.
    
    Groups are containers for users. Users must belong to a group.
    """
    lookup_field = 'gid'

    def list(self, request):  # noqa
        """
        List all Jasmin groups.
        
        Returns a list of all groups with their status (enabled/disabled).
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/groups/
        ```
        
        **Example Response:**
        ```json
        {
            "groups": [
                {"name": "group1", "status": "enabled"},
                {"name": "group2", "status": "disabled"}
            ]
        }
        ```
        """
        if not hasattr(request, 'telnet'):
            return Response(data={"status": "bad request"}, status=http_status.HTTP_400_BAD_REQUEST)
        telnet = request.telnet
        telnet.sendline('group -l')
        telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = telnet.match.group(0).strip().replace("\r", '').split("\n")
        if len(result) < 3:
            return Response(data={"groups": []}, status=http_status.HTTP_200_OK)
        groups = result[2:-2]
        return Response(data={"groups": [
            {
                'name': g.strip().lstrip('!#'),
                'status': ('disabled' if g[1] == '!' else 'enabled')
            } for g in groups if g is not None
        ]})

    def create(self, request):  # noqa
        """
        Create a new Jasmin group.
        
        **Required Fields:**
        - `gid` - Group identifier (unique string)
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"gid": "mygroup"}' \\
          http://localhost:8000/api/groups/
        ```
        
        **Example Response:**
        ```json
        {"name": "mygroup"}
        ```
        """
        telnet = request.telnet
        telnet.sendline('group -a')
        telnet.expect(r'Adding a new Group(.+)\n' + INTERACTIVE_PROMPT)
        if 'gid' not in request.data:
            raise MissingKeyError('Missing gid (group identifier)')
        telnet.sendline('gid ' + request.data['gid'] + '\n')
        telnet.expect(INTERACTIVE_PROMPT)
        telnet.sendline('ok\n')

        matched_index = telnet.expect([
            r'.+Successfully added(.+)\[(.+)\][\n\r]+' + STANDARD_PROMPT,
            r'.+Error: (.+)[\n\r]+' + INTERACTIVE_PROMPT,
            r'.+(.*)(' + INTERACTIVE_PROMPT + '|' + STANDARD_PROMPT + ')',
        ])
        if matched_index == 0:
            gid = telnet.match.group(2).strip()
            telnet.sendline('persist\n')
            return Response(data={'name': gid}, status=http_status.HTTP_201_CREATED)
        else:
            raise ActionFailed(telnet.match.group(1))

    def simple_group_action(self, telnet, _action, gid):
        telnet.sendline('group -%s %s' % (_action, gid))
        matched_index = telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown Group: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            telnet.sendline('persist\n')
            return Response(data={'name': gid}, status=http_status.HTTP_200_OK)
        elif matched_index == 1:
            raise ObjectNotFoundError('Unknown group: %s' % gid)
        else:
            raise ActionFailed(telnet.match.group(1))

    def destroy(self, request, gid):
        """
        Delete a group.
        
        **URL Parameters:**
        - `gid` - Group identifier to delete
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/groups/mygroup/
        ```
        
        **Example Response:**
        ```json
        {"name": "mygroup"}
        ```
        """
        return self.simple_group_action(request.telnet, 'r', gid)

    @action(methods=['put'], detail=True)
    def enable(self, request, gid):
        """
        Enable a disabled group.
        
        **URL Parameters:**
        - `gid` - Group identifier to enable
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/groups/mygroup/enable/
        ```
        
        **Example Response:**
        ```json
        {"name": "mygroup"}
        ```
        """
        return self.simple_group_action(request.telnet, 'e', gid)

    @action(methods=['put'], detail=True)
    def disable(self, request, gid):
        """
        Disable a group (disables all users in the group).
        
        **URL Parameters:**
        - `gid` - Group identifier to disable
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/groups/mygroup/disable/
        ```
        
        **Example Response:**
        ```json
        {"name": "mygroup"}
        ```
        """
        return self.simple_group_action(request.telnet, 'd', gid)


groups_list = GroupsViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
groups_detail = GroupsViewSet.as_view({
    'delete': 'destroy',
})
groups_enable = GroupsViewSet.as_view({'put': 'enable'})
groups_disable = GroupsViewSet.as_view({'put': 'disable'})
