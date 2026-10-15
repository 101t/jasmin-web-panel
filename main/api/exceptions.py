from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """Give every API error the ``{"error": "..."}`` shape the views already return.

    ``detail`` is kept alongside for clients that expect DRF's default key.
    """
    response = drf_exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict) and 'detail' in response.data:
        response.data = {'error': str(response.data['detail']), 'detail': response.data['detail']}
    return response
