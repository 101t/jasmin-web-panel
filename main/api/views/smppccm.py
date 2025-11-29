from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status

from main.core.smpp import SMPPCCM
from main.core.exceptions import MissingKeyError, ActionFailed, ObjectNotFoundError


class SMPPCCMViewSet(ViewSet):
    """
    SMPPCCMViewSet to manage SMPP Client Connectors.
    
    SMPP connectors are used to connect to SMSC (Short Message Service Center)
    providers for sending and receiving SMS messages.
    
    **Common Fields:**
    - `cid` - Connector identifier
    - `host` - SMSC hostname/IP
    - `port` - SMSC port (usually 2775)
    - `username` - SMPP username
    - `password` - SMPP password
    - `submit_throughput` - Messages per second limit
    """
    lookup_field = 'cid'

    def list(self, request):
        """
        List all SMPP client connectors.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/smppccm/
        ```
        
        **Example Response:**
        ```json
        {"connectors": [{"cid": "smpp1", "host": "smsc.example.com", "status": "started"}]}
        ```
        """
        try:
            smppccm = SMPPCCM()
            return Response(data=smppccm.list(), status=http_status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """
        Create a new SMPP client connector.
        
        **Required Fields:**
        - `cid` - Connector identifier
        - `host` - SMSC hostname or IP
        - `port` - SMSC port
        
        **Optional Fields:**
        - `username`, `password` - SMPP credentials
        - `submit_throughput` - Rate limit (msg/sec)
        - `logfile`, `loglevel` - Logging configuration
        
        **Example Request:**
        ```bash
        curl -u admin:password -X POST \\
          -H "Content-Type: application/json" \\
          -d '{"cid": "mysmpp", "host": "smsc.example.com", "port": 2775, "username": "user", "password": "pass"}' \\
          http://localhost:8000/api/smppccm/
        ```
        """
        try:
            smppccm = SMPPCCM()
            result = smppccm.create(data=request.data)
            return Response(data=result, status=http_status.HTTP_201_CREATED)
        except MissingKeyError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, cid):
        """
        Retrieve details of a single SMPP connector.
        
        **Example Request:**
        ```bash
        curl -u admin:password http://localhost:8000/api/smppccm/mysmpp/
        ```
        """
        try:
            smppccm = SMPPCCM()
            return Response(data=smppccm.retrieve(cid), status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, cid):
        """
        Update an SMPP connector configuration.
        
        Stop the connector before updating, then start again.
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PATCH \\
          -H "Content-Type: application/json" \\
          -d '{"host": "newhost.example.com", "port": 2776}' \\
          http://localhost:8000/api/smppccm/mysmpp/
        ```
        """
        try:
            smppccm = SMPPCCM()
            result = smppccm.partial_update(data=request.data, cid=cid)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, cid):
        """
        Delete an SMPP connector.
        
        Stop the connector first before deleting.
        
        **Example Request:**
        ```bash
        curl -u admin:password -X DELETE http://localhost:8000/api/smppccm/mysmpp/
        ```
        """
        try:
            smppccm = SMPPCCM()
            result = smppccm.destroy(cid)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=True)
    def start(self, request, cid):
        """
        Start an SMPP connector (connect to SMSC).
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/smppccm/mysmpp/start/
        ```
        """
        try:
            smppccm = SMPPCCM()
            result = smppccm.start(cid)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=True)
    def stop(self, request, cid):
        """
        Stop an SMPP connector (disconnect from SMSC).
        
        **Example Request:**
        ```bash
        curl -u admin:password -X PUT http://localhost:8000/api/smppccm/mysmpp/stop/
        ```
        """
        try:
            smppccm = SMPPCCM()
            result = smppccm.stop(cid)
            return Response(data=result, status=http_status.HTTP_200_OK)
        except ObjectNotFoundError as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        except ActionFailed as e:
            return Response(data={"error": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


smppccm_list = SMPPCCMViewSet.as_view({'get': 'list', 'post': 'create'})
smppccm_detail = SMPPCCMViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
smppccm_start = SMPPCCMViewSet.as_view({'put': 'start'})
smppccm_stop = SMPPCCMViewSet.as_view({'put': 'stop'})
