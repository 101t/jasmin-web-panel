from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import HTTPCCM


class HTTPCCMViewSet(ViewSet):
    """HTTPCCMViewSet to manage HTTP Client Connectors."""
    lookup_field = 'cid'

    def list(self, request):
        """List all HTTP client connectors."""
        with HTTPCCM() as httpccm:
            return Response(data=httpccm.list(), status=http_status.HTTP_200_OK)

    def create(self, request):
        """Create a new HTTP client connector."""
        with HTTPCCM() as httpccm:
            return Response(data=httpccm.create(data=request.data), status=http_status.HTTP_201_CREATED)

    def retrieve(self, request, cid):
        """Retrieve details of a single HTTP connector."""
        with HTTPCCM() as httpccm:
            return Response(data=httpccm.retrieve(cid), status=http_status.HTTP_200_OK)

    def destroy(self, request, cid):
        """Delete an HTTP connector."""
        with HTTPCCM() as httpccm:
            return Response(data=httpccm.destroy(cid), status=http_status.HTTP_200_OK)


httpccm_list = HTTPCCMViewSet.as_view({'get': 'list', 'post': 'create'})
httpccm_detail = HTTPCCMViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
