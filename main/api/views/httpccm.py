from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import HTTPCCM
from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError


class HTTPCCMViewSet(ViewSet):
    """
    HTTPCCMViewSet to manage HTTP Client Connectors.
    
    HTTP connectors are used to receive MO (Mobile Originated) messages
    via HTTP callbacks to your application.
    """
    lookup_field = 'cid'

    def list(self, request):
        """
        List all HTTP client connectors.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/httpccm/
        ```
        
        **Example Response:**
        ```json
        {"connectors": [{"cid": "http1", "url": "http://example.com/receive"}]}
        ```
        """
        try:
            httpccm = HTTPCCM()
            return Response(data=httpccm.list(), status=http_status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """
        Create a new HTTP client connector.
        
        **Required Fields:**
        - `cid` - Connector identifier
        - `url` - Callback URL for receiving messages
        - `method` - HTTP method (GET or POST)
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"cid": "myhttp", "url": "http://example.com/receive", "method": "POST"}' \\
          http://localhost:8000/api/httpccm/
        ```
        
        **Example Response:**
        ```json
        {"cid": "myhttp"}
        ```
        """
        try:
            httpccm = HTTPCCM()
            result = httpccm.create(data=request.data)
            return Response(data=result, status=http_status.HTTP_201_CREATED)
        except MissingKeyError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, cid):
        """
        Retrieve details of a single HTTP connector.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/httpccm/myhttp/
        ```
        """
        try:
            httpccm = HTTPCCM()
            return Response(data=httpccm.retrieve(cid), status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)

    def destroy(self, request, cid):
        """
        Delete an HTTP connector.
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/httpccm/myhttp/
        ```
        """
        try:
            httpccm = HTTPCCM()
            result = httpccm.destroy(cid)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


httpccm_list = HTTPCCMViewSet.as_view({'get': 'list', 'post': 'create'})
httpccm_detail = HTTPCCMViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
