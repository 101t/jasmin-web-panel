from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import MTRouter


class MTRouterViewSet(ViewSet):
    """MTRouterViewSet to manage MT (Mobile Terminated) Routes."""
    lookup_field = 'order'

    def list(self, request):
        """List all MT (Mobile Terminated) routes."""
        with MTRouter() as mtrouter:
            return Response(data=mtrouter.list(), status=http_status.HTTP_200_OK)

    def create(self, request):
        """Create a new MT route."""
        with MTRouter() as mtrouter:
            return Response(data=mtrouter.create(data=request.data), status=http_status.HTTP_201_CREATED)

    def retrieve(self, request, order):
        """Retrieve details of a single MT route."""
        with MTRouter() as mtrouter:
            return Response(data=mtrouter.retrieve(order), status=http_status.HTTP_200_OK)

    def destroy(self, request, order):
        """Delete an MT route."""
        with MTRouter() as mtrouter:
            return Response(data=mtrouter.destroy(order), status=http_status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def flush(self, request):
        """Flush (delete) all MT routes."""
        with MTRouter() as mtrouter:
            return Response(data=mtrouter.flush(), status=http_status.HTTP_200_OK)


mtrouter_list = MTRouterViewSet.as_view({'get': 'list', 'post': 'create'})
mtrouter_detail = MTRouterViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
mtrouter_flush = MTRouterViewSet.as_view({'post': 'flush'})
