from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """
    Jasmin Web Panel API Root
    
    Browse all available API endpoints for managing the Jasmin SMS Gateway.
    
    **Authentication:**
    - Session Auth (login to web panel first)
    - Basic Auth: `curl -u username:password http://localhost:8000/api/`
    
    **Available Endpoints:**
    - `groups` - Manage user groups
    - `users` - Manage Jasmin users
    - `filters` - Manage message filters
    - `httpccm` - Manage HTTP connectors (for MO routing)
    - `smppccm` - Manage SMPP connectors (for MT routing)
    - `morouter` - Manage MO (incoming) routes
    - `mtrouter` - Manage MT (outgoing) routes
    - `health_check` - API health status
    
    **Example Request:**
    ```bash
    curl -u admin:password http://localhost:8000/api/
    ```
    """
    return Response({
        'groups': reverse('api:groups_list', request=request, format=format),
        'users': reverse('api:users_list', request=request, format=format),
        'filters': reverse('api:filters_list', request=request, format=format),
        'httpccm': reverse('api:httpccm_list', request=request, format=format),
        'smppccm': reverse('api:smppccm_list', request=request, format=format),
        'morouter': reverse('api:morouter_list', request=request, format=format),
        'mtrouter': reverse('api:mtrouter_list', request=request, format=format),
        'health_check': reverse('api:health_check', request=request, format=format),
    })
