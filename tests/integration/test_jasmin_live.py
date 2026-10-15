"""
End-to-end tests of the jcli layer against a real Jasmin gateway.

Skipped unless JASMIN_INTEGRATION=1. Point TELNET_HOST / TELNET_PORT at a disposable gateway:
the tests create and then remove their own groups, users, connectors, filters and routes.

    docker compose -f tests/integration/docker-compose.yml up -d --wait
    JASMIN_INTEGRATION=1 TELNET_PORT=18990 pytest tests/integration -v
"""
import os
import uuid

import pytest

from main.core.exceptions import (
    DuplicateEntryError,
    JasminError,
    MultipleValuesRequiredKeyError,
    ObjectNotFoundError,
    TelnetLoginFailed,
    TelnetUnexpectedResponse,
    ValidationError,
)
from main.core.smpp import Filters, Groups, HTTPCCM, MORouter, MTRouter, SMPPCCM, Users

pytestmark = pytest.mark.skipif(
    os.environ.get('JASMIN_INTEGRATION') != '1',
    reason='set JASMIN_INTEGRATION=1 to run against a live Jasmin gateway',
)

# jcli ids are limited in length and charset; keep them short and unique per run.
RUN = uuid.uuid4().hex[:6]
GID, UID, USERNAME = 'g_%s' % RUN, 'u_%s' % RUN, 'n%s' % RUN
SMPP1, SMPP2, HTTP1 = 'smpp1_%s' % RUN, 'smpp2_%s' % RUN, 'http_%s' % RUN
F_USER, F_ALL, F_MSG = 'fu_%s' % RUN, 'ft_%s' % RUN, 'fm_%s' % RUN


@pytest.fixture(scope='module', autouse=True)
def gateway_objects():
    """Create the shared objects once, and remove them whatever the outcome."""
    with Groups() as groups:
        groups.create({'gid': GID})
    with Users() as users:
        users.create({'uid': UID, 'gid': GID, 'username': USERNAME, 'password': 'pw%s' % RUN})
    with SMPPCCM() as smppccm:
        for cid in (SMPP1, SMPP2):
            smppccm.create({'cid': cid, 'host': '127.0.0.1', 'port': '2775', 'username': 'x', 'password': 'y'})
    with HTTPCCM() as httpccm:
        httpccm.create({'cid': HTTP1, 'url': 'http://127.0.0.1/mo', 'method': 'GET'})
    with Filters() as filters:
        filters.create({'type': 'userfilter', 'fid': F_USER, 'parameter': UID})
        filters.create({'type': 'transparentfilter', 'fid': F_ALL})
        filters.create({'type': 'shortmessagefilter', 'fid': F_MSG, 'parameter': '^hello, <world>$'})
    yield
    for manager, items in ((MTRouter, ['20', '21', '0']), (MORouter, ['30', '31'])):
        with manager() as m:
            for order in items:
                try:
                    m.destroy(order)
                except ObjectNotFoundError:
                    pass
    cleanup = ((Filters, (F_USER, F_ALL, F_MSG)), (HTTPCCM, (HTTP1,)), (SMPPCCM, (SMPP1, SMPP2)),
               (Users, (UID,)), (Groups, (GID,)))
    for manager, ids in cleanup:
        with manager() as m:
            for item in ids:
                try:
                    m.destroy(item)
                except ObjectNotFoundError:
                    pass


class TestConnection:
    def test_wrong_password_fails_fast(self, settings):
        settings.TELNET_PW = 'definitely-wrong'
        with pytest.raises(TelnetLoginFailed):
            Groups()

    def test_unreachable_gateway(self, settings):
        settings.TELNET_PORT = 1
        with pytest.raises(TelnetUnexpectedResponse):
            Groups()

    def test_line_breaks_are_rejected(self):
        with Groups() as groups, pytest.raises(ValidationError):
            groups.create({'gid': 'x\ngroup -r %s' % GID})


class TestGroups:
    def test_listed(self):
        with Groups() as groups:
            assert {'name': GID, 'status': 'enabled'} in groups.list()['groups']

    def test_duplicate_is_refused(self):
        """jcli would silently replace the existing group."""
        with Groups() as groups, pytest.raises(DuplicateEntryError):
            groups.create({'gid': GID})

    def test_disable_enable(self):
        with Groups() as groups:
            groups.disable(GID)
            assert {'name': GID, 'status': 'disabled'} in groups.list()['groups']
            groups.enable(GID)
            assert {'name': GID, 'status': 'enabled'} in groups.list()['groups']

    def test_unknown_group_is_not_found(self):
        with Groups() as groups, pytest.raises(ObjectNotFoundError):
            groups.disable('nope_%s' % RUN)


class TestUsers:
    def test_retrieve_parses_credentials(self):
        with Users() as users:
            user = users.retrieve(UID)['user']
        assert user['gid'] == GID and user['username'] == USERNAME
        assert user['mt_messaging_cred']['authorization']['http_send'] == 'True'
        assert user['mt_messaging_cred']['valuefilter']['priority'] == '^[0-3]$'
        assert user['mt_messaging_cred']['quota']['balance'] == 'ND'
        assert 'password' not in user

    def test_duplicate_does_not_reset_the_user(self):
        """jcli would replace the user and reset its quotas and authorizations."""
        with Users() as users:
            users.partial_update([['mt_messaging_cred', 'quota', 'sms_count', '42']], uid=UID)
            with pytest.raises(DuplicateEntryError):
                users.create({'uid': UID, 'gid': GID, 'username': 'other%s' % RUN, 'password': 'p'})
            user = users.retrieve(UID)['user']
        assert user['username'] == USERNAME
        assert user['mt_messaging_cred']['quota']['sms_count'] == '42'

    def test_unknown_group_is_reported(self):
        with Users() as users, pytest.raises(JasminError, match='Unknown Group'):
            users.create({'uid': 'x_%s' % RUN, 'gid': 'nope', 'username': 'x%s' % RUN, 'password': 'p'})

    def test_update_authorization_and_quota(self):
        with Users() as users:
            user = users.partial_update([
                ['mt_messaging_cred', 'authorization', 'http_send', 'False'],
                ['mt_messaging_cred', 'quota', 'balance', '100'],
            ], uid=UID)['user']
            assert user['mt_messaging_cred']['authorization']['http_send'] == 'False'
            assert user['mt_messaging_cred']['quota']['balance'] == '100.0'
            user = users.partial_update([['mt_messaging_cred', 'quota', 'balance', 'None']], uid=UID)['user']
            assert user['mt_messaging_cred']['quota']['balance'] == 'ND'

    def test_rejected_update_is_reported_and_connection_recovers(self):
        with Users() as users:
            with pytest.raises(JasminError, match='could not convert'):
                users.partial_update([['mt_messaging_cred', 'quota', 'balance', 'ND']], uid=UID)
            with pytest.raises(JasminError, match='can not be modified'):
                users.partial_update([['username', 'other']], uid=UID)
            # The aborted sessions must not leave jcli in interactive mode.
            assert users.retrieve(UID)['user']['uid'] == UID

    def test_list_and_status(self):
        with Users() as users:
            users.disable(UID)
            listed = {u['uid']: u for u in users.list()['users']}
            assert listed[UID]['status'] == 'disabled'
            users.enable(UID)

    def test_unknown_user_is_not_found(self):
        with Users() as users, pytest.raises(ObjectNotFoundError):
            users.retrieve('nope_%s' % RUN)


class TestConnectors:
    def test_smppccm_listed_with_status(self):
        with SMPPCCM() as smppccm:
            listed = {c['cid']: c for c in smppccm.list()['connectors']}
        assert listed[SMPP1]['status'] == 'stopped'
        assert listed[SMPP1]['host'] == '127.0.0.1'
        assert listed[SMPP1]['systype'] == ''

    def test_smppccm_update_only_sends_changes(self):
        with SMPPCCM() as smppccm:
            current = smppccm.retrieve(SMPP1)['connector']
            current['submit_throughput'] = '5'
            updated = smppccm.partial_update(current, cid=SMPP1)['connector']
            assert updated['submit_throughput'] == '5'

    def test_smppccm_invalid_value_is_reported(self):
        with SMPPCCM() as smppccm:
            with pytest.raises(JasminError):
                smppccm.partial_update({'port': 'not-a-number'}, cid=SMPP1)
            assert smppccm.retrieve(SMPP1)['connector']['port'] == '2775'

    def test_smppccm_unknown_is_not_found(self):
        with SMPPCCM() as smppccm, pytest.raises(ObjectNotFoundError):
            smppccm.stop('nope_%s' % RUN)

    def test_httpccm(self):
        with HTTPCCM() as httpccm:
            listed = {c['cid']: c for c in httpccm.list()['connectors']}
            assert listed[HTTP1] == {'cid': HTTP1, 'type': 'HttpConnector', 'method': 'GET',
                                     'url': 'http://127.0.0.1/mo'}
            assert httpccm.retrieve(HTTP1)['connector']['baseurl'] == 'http://127.0.0.1/mo'
            with pytest.raises(JasminError):
                httpccm.create({'cid': 'bad_%s' % RUN, 'url': 'http://x/', 'method': 'PUT'})


class TestFilters:
    def test_listed_with_routes_and_description(self):
        with Filters() as filters:
            listed = {f['fid']: f for f in filters.list()['filters']}
        assert listed[F_USER] == {'fid': F_USER, 'type': 'UserFilter', 'routes': 'MT',
                                  'description': '<U (uid=%s)>' % UID}
        assert listed[F_ALL]['routes'] == 'MO MT'
        assert listed[F_MSG]['description'].startswith('<SM (msg=^hello, <world>$)')

    def test_unknown_filter_is_not_found(self):
        with Filters() as filters, pytest.raises(ObjectNotFoundError):
            filters.destroy('nope_%s' % RUN)


class TestRouters:
    def test_mt_round_robin_with_several_connectors(self):
        """Issue #107: several connectors and filters from a multi-select."""
        with MTRouter() as mtrouter:
            route = mtrouter.create({
                'type': 'RandomRoundrobinMTRoute', 'order': '20', 'rate': '1.5',
                'smppconnectors': [SMPP1, SMPP2], 'filters': [F_USER, F_MSG],
            })['mtrouter']
        assert route['connectors'] == ['smppc(%s)' % SMPP1, 'smppc(%s)' % SMPP2]
        assert route['filters'][0] == '<U (uid=%s)>' % UID
        assert route['filters'][1].startswith('<SM (msg=^hello, <world>$)')
        assert route['rate'] == '1.50000'

    def test_mt_default_route_is_order_zero(self):
        with MTRouter() as mtrouter:
            route = mtrouter.create({'type': 'DefaultRoute', 'order': '9', 'smppconnectors': SMPP1})['mtrouter']
        assert route['order'] == '0' and route['filters'] == []

    def test_mt_duplicate_order_and_connector_count(self):
        with MTRouter() as mtrouter:
            with pytest.raises(DuplicateEntryError):
                mtrouter.create({'type': 'StaticMTRoute', 'order': '20', 'smppconnectors': SMPP1,
                                 'filters': F_USER})
            with pytest.raises(MultipleValuesRequiredKeyError):
                mtrouter.create({'type': 'FailoverMTRoute', 'order': '21', 'smppconnectors': SMPP1,
                                 'filters': F_USER})

    def test_mo_route_to_smpp_server_user(self):
        with MORouter() as morouter:
            route = morouter.create({'type': 'StaticMORoute', 'order': '30', 'smppconnectors': [USERNAME],
                                     'filters': [F_ALL]})['morouter']
        assert route['connectors'] == ['smpps(%s)' % USERNAME]
        assert route['filters'] == ['<T>']

    def test_mo_rejections_are_reported(self):
        with MORouter() as morouter:
            with pytest.raises(JasminError, match='not a valid filter for MORoute'):
                morouter.create({'type': 'StaticMORoute', 'order': '31', 'httpconnectors': HTTP1,
                                 'filters': F_USER})
            with pytest.raises(JasminError, match='mixed connector types'):
                morouter.create({'type': 'FailoverMORoute', 'order': '31', 'smppconnectors': USERNAME,
                                 'httpconnectors': HTTP1, 'filters': F_ALL})
            assert not morouter.router_exists('31')
