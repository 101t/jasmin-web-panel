from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import Groups


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
        with Groups() as groups:
            return Response(data=groups.list(), status=http_status.HTTP_200_OK)

    def create(self, request):  # noqa
        """
        Create a new group.

        **Required Fields:**
        - `gid` - Group identifier

        **Example Request:**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"gid": "group1"}' \\
          http://localhost:8000/api/groups/
        ```

        **Example Response:**
        ```json
        {"name": "group1"}
        ```
        """
        with Groups() as groups:
            return Response(data=groups.create(request.data), status=http_status.HTTP_201_CREATED)

    def destroy(self, request, gid):
        """
        Delete a group.

        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/groups/group1/
        ```
        """
        with Groups() as groups:
            return Response(data=groups.destroy(gid), status=http_status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def enable(self, request, gid):
        """
        Enable a disabled group.

        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/groups/group1/enable/
        ```
        """
        with Groups() as groups:
            return Response(data=groups.enable(gid), status=http_status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def disable(self, request, gid):
        """
        Disable a group (and with it the users it contains).

        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/groups/group1/disable/
        ```
        """
        with Groups() as groups:
            return Response(data=groups.disable(gid), status=http_status.HTTP_200_OK)


groups_list = GroupsViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
groups_detail = GroupsViewSet.as_view({
    'delete': 'destroy',
})
groups_enable = GroupsViewSet.as_view({'put': 'enable'})
groups_disable = GroupsViewSet.as_view({'put': 'disable'})
