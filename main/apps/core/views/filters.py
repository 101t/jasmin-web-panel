from collections import OrderedDict

from django.conf import settings
from django.http import JsonResponse
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import list_route

from main.apps.core.tools import set_ikeys, split_cols
from main.apps.core.exceptions import (JasminSyntaxError, JasminError,
                        UnknownError, MissingKeyError,
                        MutipleValuesRequiredKeyError, ObjectNotFoundError)

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

class FiltersViewSet(ViewSet):
    "Viewset for managing Filters"
    lookup_field = 'fid'

    def _list(self, telnet):
        "List Filters as python dict"
        telnet.sendline('filter -l')
        telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = telnet.match.group(0).strip().replace("\r", '').split("\n")
        if len(result) < 3:
            return {'filters': []}
        results = [l.replace(', ', ',').replace('(!)', '')
            for l in result[2:-2] if l]
        filters = split_cols(results)
        return {
            'filters':
                [
                    {
                        'fid': f[0].strip().lstrip('#'),
                        'type': f[1],
                        'routes': f[2] + ' ' + f[3],
                        'description': ' '.join(f[4:])
                    } for f in filters
                ]
        }

    def list(self, request):
        "List Filters. No parameters"
        return JsonResponse(self._list(request.telnet))

    def get_filter(self, telnet, fid):
        "Return data for one filter as Python dict"
        filters = self._list(telnet)['filters']
        try:
            return {'filter':
                next((m for m in filters if m['fid'] == fid), None)
            }
        except StopIteration:
            raise ObjectNotFoundError('No Filter with fid: %s' % fid)

    def retrieve(self, request, fid):
        "Details for one Filter by fid (integer)"
        return JsonResponse(self.get_filter(request.telnet, fid))

    def create(self, request):
        """Create Filter.
        Required parameters: type, fid, parameters
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: type
          description: One of TransparentFilter, ConnectorFilter, UserFilter, GroupFilter, SourceAddrFilter, DestinationAddrFilter, ShortMessageFilter, DateIntervalFilter, TimeIntervalFilter, TagFilter, EvalPyFilter
          required: true
          type: string
          paramType: form
        - name: fid
          description: Filter id, used to identify filter
          required: true
          type: string
          paramType: form
        - name: parameter
          description: Parameter
          required: false
          type: string
          paramType: form
        """
        telnet = request.telnet
        data = request.data
        try:
            ftype, fid = data['type'], data['fid']
        except IndexError:
            raise MissingKeyError(
                'Missing parameter: type or fid required')
        ftype = ftype.lower()
        telnet.sendline('filter -a')
        telnet.expect(r'Adding a new Filter(.+)\n' + INTERACTIVE_PROMPT)
        ikeys = OrderedDict({'type': ftype, 'fid': fid})
        if ftype != 'transparentfilter':
            try:
                parameter = data['parameter']
            except MultiValueDictKeyError:
                raise MissingKeyError('%s filter requires parameter' % ftype)
            if ftype == 'connectorfilter':
                ikeys['cid'] = parameter
            elif ftype == 'userfilter':
                ikeys['uid'] = parameter
            elif ftype == 'groupfilter':
                ikeys['gid'] = parameter
            elif ftype == 'sourceaddrfilter':
                ikeys['source_addr'] = parameter
            elif ftype == 'destinationaddrfilter':
                ikeys['destination_addr'] = parameter
            elif ftype == 'shortmessagefilter':
                ikeys['short_message'] = parameter
            elif ftype == 'dateintervalfilter':
                ikeys['dateInterval'] = parameter
            elif ftype == 'timeintervalfilter':
                ikeys['timeInterval'] = parameter
            elif ftype == 'tagfilter':
                ikeys['tag'] = parameter
            elif ftype == 'evalpyfilter':
                ikeys['pyCode'] = parameter
        print ikeys
        set_ikeys(telnet, ikeys)
        telnet.sendline('persist\n')
        telnet.expect(r'.*' + STANDARD_PROMPT)
        return JsonResponse({'filter': self.get_filter(telnet, fid)})

    def simple_filter_action(self, telnet, action, fid, return_filter=True):
        telnet.sendline('filter -%s %s' % (action, fid))
        matched_index = telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown Filter: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            telnet.sendline('persist\n')
            if return_filter:
                telnet.expect(r'.*' + STANDARD_PROMPT)
                return JsonResponse({'filter': self.get_filter(telnet, fid)})
            else:
                return JsonResponse({'fid': fid})
        elif matched_index == 1:
            raise UnknownError(detail='No filter:' +  fid)
        else:
            raise JasminError(telnet.match.group(1))

    def destroy(self, request, fid):
        """Delete a filter. One parameter required, the filter identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent filter
        - 400: other error
        """
        return self.simple_filter_action(
            request.telnet, 'r', fid, return_filter=False)
