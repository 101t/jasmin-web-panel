from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import MTRouter
from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError


class MTRouterViewSet(ViewSet):
    """
    MTRouterViewSet to manage MT (Mobile Terminated) Routes.
    
    MT Routes determine how outgoing messages are routed to SMPP connectors.
    
    **Router Types:**
    - `DefaultRoute` - Catch-all route (order=0)
    - `StaticMTRoute` - Static route with filters
    - `RandomRoundrobinMTRoute` - Load balance across connectors
    - `FailoverMTRoute` - Failover between connectors
    """
    lookup_field = 'order'

    def list(self, request):
        """
        List all MT (Mobile Terminated) routes.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/mtrouter/
        ```
        
        **Example Response:**
        ```json
        {"routers": [{"order": "0", "type": "DefaultRoute", "connector": "smppc(smpp1)", "rate": "0.00"}]}
        ```
        """
        try:
            mtrouter = MTRouter()
            return Response(data=mtrouter.list(), status=http_status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """
        Create a new MT route.
        
        **Required Fields:**
        - `type` - Router type
        - `connector` - SMPP connector ID (e.g., "smppc(mysmpp)")
        - `order` - Route priority (lower = higher priority, 0 for DefaultRoute)
        
        **Optional Fields:**
        - `filters` - Filter ID for matching messages
        - `rate` - Cost per message (for billing)
        
        **Example Request (Default Route):**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"type": "DefaultRoute", "connector": "smppc(mysmpp)", "rate": "0.00"}' \\
          http://localhost:8000/api/mtrouter/
        ```
        
        **Example Request (Static Route with filter):**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"type": "StaticMTRoute", "order": "10", "connector": "smppc(mysmpp)", "filters": "myfilter", "rate": "0.015"}' \\
          http://localhost:8000/api/mtrouter/
        ```
        """
        try:
            mtrouter = MTRouter()
            result = mtrouter.create(data=request.data)
            return Response(data=result, status=http_status.HTTP_201_CREATED)
        except MissingKeyError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, order):
        """
        Retrieve details of a single MT route.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/mtrouter/10/
        ```
        """
        try:
            mtrouter = MTRouter()
            return Response(data=mtrouter.retrieve(order), status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)

    def destroy(self, request, order):
        """
        Delete an MT route.
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/mtrouter/10/
        ```
        """
        try:
            mtrouter = MTRouter()
            result = mtrouter.destroy(order)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def flush(self, request):
        """
        Flush (delete) all MT routes.
        
        **Warning:** This removes all MT routing rules!
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST http://localhost:8000/api/mtrouter/flush/
        ```
        """
        try:
            mtrouter = MTRouter()
            result = mtrouter.flush()
            return Response(data=result, status=http_status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


mtrouter_list = MTRouterViewSet.as_view({'get': 'list', 'post': 'create'})
mtrouter_detail = MTRouterViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
mtrouter_flush = MTRouterViewSet.as_view({'post': 'flush'})
