from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import SMPPCCM


def _redact_connector_secret(connector):
    if isinstance(connector, dict) and connector.get('password'):
        return {**connector, 'password': '********'}
    return connector


class SMPPCCMViewSet(ViewSet):
    """
    SMPPCCMViewSet to manage SMPP Client Connectors.

    SMPP connectors connect to SMSC providers for sending and receiving SMS messages.
    Connector passwords are masked in read responses.
    """
    lookup_field = 'cid'

    def list(self, request):
        """List all SMPP client connectors."""
        with SMPPCCM() as smppccm:
            data = smppccm.list()
        if isinstance(data, dict) and 'connectors' in data:
            data = {**data, 'connectors': [_redact_connector_secret(c) for c in data['connectors']]}
        return Response(data=data, status=http_status.HTTP_200_OK)

    def create(self, request):
        """Create a new SMPP client connector."""
        with SMPPCCM() as smppccm:
            return Response(data=smppccm.create(data=request.data), status=http_status.HTTP_201_CREATED)

    def retrieve(self, request, cid):
        """Retrieve details of a single SMPP connector."""
        with SMPPCCM() as smppccm:
            data = smppccm.retrieve(cid)
        if isinstance(data, dict) and 'connector' in data:
            data = {**data, 'connector': _redact_connector_secret(data['connector'])}
        return Response(data=data, status=http_status.HTTP_200_OK)

    def partial_update(self, request, cid):
        """Update an SMPP connector configuration."""
        with SMPPCCM() as smppccm:
            data = smppccm.partial_update(data=request.data, cid=cid)
        if isinstance(data, dict) and 'connector' in data:
            data = {**data, 'connector': _redact_connector_secret(data['connector'])}
        return Response(data=data, status=http_status.HTTP_200_OK)

    def destroy(self, request, cid):
        """Delete an SMPP connector."""
        with SMPPCCM() as smppccm:
            return Response(data=smppccm.destroy(cid), status=http_status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def start(self, request, cid):
        """Start an SMPP connector (connect to SMSC)."""
        with SMPPCCM() as smppccm:
            return Response(data=smppccm.start(cid), status=http_status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def stop(self, request, cid):
        """Stop an SMPP connector (disconnect from SMSC)."""
        with SMPPCCM() as smppccm:
            return Response(data=smppccm.stop(cid), status=http_status.HTTP_200_OK)


smppccm_list = SMPPCCMViewSet.as_view({'get': 'list', 'post': 'create'})
smppccm_detail = SMPPCCMViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
smppccm_start = SMPPCCMViewSet.as_view({'put': 'start'})
smppccm_stop = SMPPCCMViewSet.as_view({'put': 'stop'})
