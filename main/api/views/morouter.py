from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import MORouter
from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError


class MORouterViewSet(ViewSet):
    """
    MORouterViewSet to manage MO (Mobile Originated) Routes.
    
    MO Routes determine how incoming messages are delivered: to HTTP connectors, or to users
    bound to Jasmin's SMPP server.

    **Router Types:**
    - `DefaultRoute` - Catch-all route (order=0)
    - `StaticMORoute` - Static route with filters
    - `RandomRoundrobinMORoute` - Load balance across connectors
    - `FailoverMORoute` - Failover between connectors
    """
    lookup_field = 'order'

    def list(self, request):
        """
        List all MO (Mobile Originated) routes.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/morouter/
        ```
        
        **Example Response:**
        ```json
        {"morouters": [{"order": "0", "type": "DefaultRoute", "connectors": ["http(http1)"], "filters": []}]}
        ```
        """
        try:
            morouter = MORouter()
            return Response(data=morouter.list(), status=http_status.HTTP_200_OK)
        except APIException as e:
            return Response(data={"error": str(e.detail)}, status=e.status_code)

    def create(self, request):
        """
        Create a new MO route.
        
        **Fields:**
        - `type` - `DefaultRoute`, `StaticMORoute`, `RandomRoundrobinMORoute` or `FailoverMORoute`
        - `order` - Route priority (higher order is evaluated first; DefaultRoute is always 0)
        - `httpconnectors` - HTTP connector ids, delivered as `http(cid)`
        - `smppconnectors` - usernames of users bound to Jasmin's SMPP server, delivered as `smpps(username)`
        - `filters` - Filter ids (MO-compatible filters only); required except for DefaultRoute

        Lists may be JSON arrays or comma-separated strings. Static and Default routes take exactly
        one connector, RoundRobin and Failover at least two (Failover cannot mix HTTP and SMPP).

        **Example Request (Default Route):**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"type": "DefaultRoute", "httpconnectors": ["myhttp"]}' \\
          http://localhost:8000/api/morouter/
        ```

        **Example Request (Static Route with filter):**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"type": "StaticMORoute", "order": "10", "smppconnectors": ["bob"], "filters": ["myfilter"]}' \\
          http://localhost:8000/api/morouter/
        ```
        """
        try:
            morouter = MORouter()
            result = morouter.create(data=request.data)
            return Response(data=result, status=http_status.HTTP_201_CREATED)
        except MissingKeyError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
        except APIException as e:
            return Response(data={"error": str(e.detail)}, status=e.status_code)

    def retrieve(self, request, order):
        """
        Retrieve details of a single MO route.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/morouter/10/
        ```
        """
        try:
            morouter = MORouter()
            return Response(data=morouter.retrieve(order), status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)

    def destroy(self, request, order):
        """
        Delete an MO route.
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/morouter/10/
        ```
        """
        try:
            morouter = MORouter()
            result = morouter.destroy(order)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def flush(self, request):
        """
        Flush (delete) all MO routes.
        
        **Warning:** This removes all MO routing rules!
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST http://localhost:8000/api/morouter/flush/
        ```
        """
        try:
            morouter = MORouter()
            result = morouter.flush()
            return Response(data=result, status=http_status.HTTP_200_OK)
        except APIException as e:
            return Response(data={"error": str(e.detail)}, status=e.status_code)


morouter_list = MORouterViewSet.as_view({'get': 'list', 'post': 'create'})
morouter_detail = MORouterViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
morouter_flush = MORouterViewSet.as_view({'post': 'flush'})
