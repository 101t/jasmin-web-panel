from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import MORouter


class MORouterViewSet(ViewSet):
    """MORouterViewSet to manage MO (Mobile Originated) Routes."""
    lookup_field = 'order'

    def list(self, request):
        """List all MO (Mobile Originated) routes."""
        with MORouter() as morouter:
            return Response(data=morouter.list(), status=http_status.HTTP_200_OK)

    def create(self, request):
        """Create a new MO route."""
        with MORouter() as morouter:
            return Response(data=morouter.create(data=request.data), status=http_status.HTTP_201_CREATED)

    def retrieve(self, request, order):
        """Retrieve details of a single MO route."""
        with MORouter() as morouter:
            return Response(data=morouter.retrieve(order), status=http_status.HTTP_200_OK)

    def destroy(self, request, order):
        """Delete an MO route."""
        with MORouter() as morouter:
            return Response(data=morouter.destroy(order), status=http_status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def flush(self, request):
        """Flush (delete) all MO routes."""
        with MORouter() as morouter:
            return Response(data=morouter.flush(), status=http_status.HTTP_200_OK)


morouter_list = MORouterViewSet.as_view({'get': 'list', 'post': 'create'})
morouter_detail = MORouterViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
morouter_flush = MORouterViewSet.as_view({'post': 'flush'})
