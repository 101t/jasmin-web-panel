from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import Filters


class FiltersViewSet(ViewSet):
    """
    FiltersViewSet to manage Jasmin message filters.
    
    Filters are used in routing rules to match messages based on various criteria.
    
    **Filter Types:**
    - `TransparentFilter` - Matches all messages
    - `UserFilter` - Matches by user (`parameter`: `uid`)
    - `GroupFilter` - Matches by group (`parameter`: `gid`)
    - `ConnectorFilter` - Matches by connector (`parameter`: `cid`)
    - `SourceAddrFilter` - Matches source address regex (`parameter`: regex)
    - `DestinationAddrFilter` - Matches destination regex (`parameter`: regex)
    - `ShortMessageFilter` - Matches message content regex (`parameter`: regex)
    - `TagFilter` - Matches by tag (`parameter`: tag)
    """
    lookup_field = 'fid'

    def list(self, request):
        """List all Jasmin filters."""
        with Filters() as filters:
            return Response(data=filters.list(), status=http_status.HTTP_200_OK)

    def create(self, request):
        """
        Create a new filter.

        **Required Fields:**
        - `fid` - Filter identifier
        - `type` - Filter type (see class docstring for types)
        - `parameter` - Type-specific filter value (required for all types except `TransparentFilter`)
        """
        with Filters() as filters:
            return Response(data=filters.create(data=request.data), status=http_status.HTTP_201_CREATED)

    def retrieve(self, request, fid):
        """Retrieve details of a single filter."""
        with Filters() as filters:
            return Response(data=filters.retrieve(fid), status=http_status.HTTP_200_OK)

    def destroy(self, request, fid):
        """Delete a filter."""
        with Filters() as filters:
            return Response(data=filters.destroy(fid), status=http_status.HTTP_200_OK)


filters_list = FiltersViewSet.as_view({'get': 'list', 'post': 'create'})
filters_detail = FiltersViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
