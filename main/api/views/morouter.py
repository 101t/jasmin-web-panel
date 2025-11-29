from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import MORouter
from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError


class MORouterViewSet(ViewSet):
    """
    MORouterViewSet to manage MO (Mobile Originated) Routes.
    
    MO Routes determine how incoming messages are routed to HTTP connectors.
    
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
        {"routers": [{"order": "0", "type": "DefaultRoute", "connector": "http1"}]}
        ```
        """
        try:
            morouter = MORouter()
            return Response(data=morouter.list(), status=http_status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """
        Create a new MO route.
        
        **Required Fields:**
        - `type` - Router type
        - `connector` - HTTP connector ID (e.g., "http(myhttp)")
        - `order` - Route priority (lower = higher priority, 0 for DefaultRoute)
        
        **Optional Fields:**
        - `filters` - Filter ID for matching messages
        
        **Example Request (Default Route):**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"type": "DefaultRoute", "connector": "http(myhttp)"}' \\
          http://localhost:8000/api/morouter/
        ```
        
        **Example Request (Static Route with filter):**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"type": "StaticMORoute", "order": "10", "connector": "http(myhttp)", "filters": "myfilter"}' \\
          http://localhost:8000/api/morouter/
        ```
        """
        try:
            morouter = MORouter()
            result = morouter.create(data=request.data)
            return Response(data=result, status=http_status.HTTP_201_CREATED)
        except MissingKeyError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

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
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


morouter_list = MORouterViewSet.as_view({'get': 'list', 'post': 'create'})
morouter_detail = MORouterViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
morouter_flush = MORouterViewSet.as_view({'post': 'flush'})
