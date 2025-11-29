from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import Filters
from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError


class FiltersViewSet(ViewSet):
    """
    FiltersViewSet to manage Jasmin message filters.
    
    Filters are used in routing rules to match messages based on various criteria.
    
    **Filter Types:**
    - `TransparentFilter` - Matches all messages
    - `UserFilter` - Matches by user (requires `uid`)
    - `GroupFilter` - Matches by group (requires `gid`)
    - `ConnectorFilter` - Matches by connector (requires `cid`)
    - `SourceAddrFilter` - Matches source address regex (requires `source_addr`)
    - `DestinationAddrFilter` - Matches destination regex (requires `destination_addr`)
    - `ShortMessageFilter` - Matches message content regex (requires `short_message`)
    - `TagFilter` - Matches by tag (requires `tag`)
    """
    lookup_field = 'fid'

    def list(self, request):
        """
        List all Jasmin filters.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/filters/
        ```
        
        **Example Response:**
        ```json
        {"filters": [{"fid": "filter1", "type": "TransparentFilter"}]}
        ```
        """
        try:
            filters = Filters()
            return Response(data=filters.list(), status=http_status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """
        Create a new filter.
        
        **Required Fields:**
        - `fid` - Filter identifier
        - `type` - Filter type (see class docstring for types)
        
        **Type-specific fields:**
        - UserFilter: `uid`
        - GroupFilter: `gid`
        - ConnectorFilter: `cid`
        - SourceAddrFilter: `source_addr` (regex)
        - DestinationAddrFilter: `destination_addr` (regex)
        - ShortMessageFilter: `short_message` (regex)
        - TagFilter: `tag`
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"fid": "myfilter", "type": "TransparentFilter"}' \\
          http://localhost:8000/api/filters/
        ```
        
        **Example Response:**
        ```json
        {"fid": "myfilter"}
        ```
        """
        try:
            filters = Filters()
            result = filters.create(data=request.data)
            return Response(data=result, status=http_status.HTTP_201_CREATED)
        except MissingKeyError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, fid):
        """
        Retrieve details of a single filter.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/filters/myfilter/
        ```
        """
        try:
            filters = Filters()
            return Response(data=filters.retrieve(fid), status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)

    def destroy(self, request, fid):
        """
        Delete a filter.
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/filters/myfilter/
        ```
        """
        try:
            filters = Filters()
            result = filters.destroy(fid)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


filters_list = FiltersViewSet.as_view({'get': 'list', 'post': 'create'})
filters_detail = FiltersViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
