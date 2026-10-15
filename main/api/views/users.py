from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import Users


class UsersViewSet(ViewSet):
    """
    UsersViewSet to manage Jasmin users.

    Jasmin users are separate from Django authentication users.
    Each user belongs to a group and has credentials for sending SMS.
    """
    lookup_field = 'uid'

    def list(self, request):
        """
        List all Jasmin users with their credentials and status.

        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/users/
        ```

        **Example Response:**
        ```json
        {"users": [{"uid": "user1", "gid": "group1", "username": "user1", "status": "enabled",
                    "mt_messaging_cred": {"authorization": {"http_send": "True"}, "quota": {"balance": "ND"}}}]}
        ```
        """
        with Users() as users:
            return Response(data=users.list(), status=http_status.HTTP_200_OK)

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

        **Example Response:** the created user, as returned by `GET /api/users/<uid>/`.
        """
        with Users() as users:
            return Response(data=users.create(request.data), status=http_status.HTTP_201_CREATED)

    def retrieve(self, request, uid):
        """
        Retrieve one user with its credentials (password excluded).

        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/users/user1/
        ```
        """
        with Users() as users:
            return Response(data=users.retrieve(uid), status=http_status.HTTP_200_OK)

    def partial_update(self, request, uid):
        """
        Update a user. `updates` is a list of jcli `user -u` lines, each given as a list.

        **Example Request:**
        ```bash
        curl -u admin:password -X PATCH \\
          -H "Content-Type: application/json" \\
          -d '{"updates": [["gid", "group2"], ["mt_messaging_cred", "quota", "balance", "100"]]}' \\
          http://localhost:8000/api/users/user1/
        ```
        """
        with Users() as users:
            return Response(data=users.partial_update(request.data.get('updates'), uid=uid),
                            status=http_status.HTTP_200_OK)

    def destroy(self, request, uid):
        """
        Delete a user.

        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/users/user1/
        ```

        **Example Response:**
        ```json
        {"uid": "user1"}
        ```
        """
        with Users() as users:
            return Response(data=users.destroy(uid), status=http_status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def enable(self, request, uid):
        """
        Enable a disabled user.

        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/users/user1/enable/
        ```
        """
        with Users() as users:
            return Response(data=users.enable(uid), status=http_status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def disable(self, request, uid):
        """
        Disable a user (prevents SMS sending).

        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/users/user1/disable/
        ```
        """
        with Users() as users:
            return Response(data=users.disable(uid), status=http_status.HTTP_200_OK)


users_list = UsersViewSet.as_view({'get': 'list', 'post': 'create'})
users_detail = UsersViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
users_enable = UsersViewSet.as_view({'put': 'enable'})
users_disable = UsersViewSet.as_view({'put': 'disable'})
