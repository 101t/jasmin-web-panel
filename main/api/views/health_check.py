from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.version import VERSION


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    API Health Check
    
    Returns the current API version and status. No authentication required.
    
    **Example Request:**
    ```bash
    curl http://localhost:8000/api/health_check
    ```
    
    **Example Response:**
    ```json
    {"version": "1.0.0", "status": "ok"}
    ```
    """
    return Response({"version": VERSION, "status": "ok"})
