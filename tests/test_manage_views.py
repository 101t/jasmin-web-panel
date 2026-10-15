"""
Tests for the contract between the web UI and the backend: the AJAX "manage" endpoints and
the REST API, with the jcli managers replaced by fakes (no gateway needed).
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from main.core.exceptions import JasminError, ObjectNotFoundError, TelnetUnexpectedResponse
from main.core.models import GroupsModel, UsersModel
from main.web.views.content.users import user_updates

User = get_user_model()
AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


@pytest.fixture
def panel_user(db):
    return User.objects.create_superuser(username='panel', email='panel@example.com', password='pw-123456')


@pytest.fixture
def auth_client(client, panel_user):
    client.force_login(panel_user)
    return client


@pytest.fixture
def stored_user(panel_user):
    """A Jasmin user the panel created, so it knows its password (used by Send SMS)."""
    return UsersModel.objects.create(uid='u1', gid=GroupsModel.objects.create(gid='g1'), username='bob',
                                     password='old', parameters='', user=panel_user)


@pytest.fixture
def fake_manager(monkeypatch):
    """Replace a jcli manager class in a view module; returns the list of recorded calls."""
    def install(module, name, results=None):
        calls = []

        class Fake:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def __getattr__(self, method):
                def call(*args, **kwargs):
                    calls.append((method, args, kwargs))
                    result = (results or {}).get(method, {})
                    if isinstance(result, Exception):
                        raise result
                    return dict(result)
                return call

        monkeypatch.setattr(module + '.' + name, Fake)
        return calls
    return install


class TestAjaxContract:
    url = staticmethod(lambda: reverse('web:groups_view_manage'))

    def test_expired_session_gets_json_not_a_login_redirect(self, client, db):
        response = client.post(self.url(), {'s': 'list'}, **AJAX)
        assert response.status_code == 401
        assert response.json()['login_url'] == '/account/login/'

    def test_non_ajax_is_refused(self, auth_client):
        assert auth_client.post(self.url(), {'s': 'list'}).status_code == 400

    def test_jasmin_error_is_reported_with_its_message(self, auth_client, fake_manager):
        fake_manager('main.web.views.content.groups', 'Groups', {'create': JasminError('gid: Group gid syntax is invalid')})
        response = auth_client.post(self.url(), {'s': 'add', 'gid': 'bad gid'}, **AJAX)
        assert response.status_code == 400
        assert response.json() == {'message': 'gid: Group gid syntax is invalid', 'status': 400}

    def test_gateway_down_is_a_503(self, auth_client, fake_manager):
        fake_manager('main.web.views.content.groups', 'Groups', {'list': TelnetUnexpectedResponse('Jasmin is down')})
        response = auth_client.post(self.url(), {'s': 'list'}, **AJAX)
        assert response.status_code == 503
        assert response.json()['message'] == 'Jasmin is down'

    def test_unexpected_crash_is_still_json(self, auth_client, fake_manager):
        fake_manager('main.web.views.content.groups', 'Groups', {'list': RuntimeError('boom')})
        response = auth_client.post(self.url(), {'s': 'list'}, **AJAX)
        assert response.status_code == 500
        assert 'message' in response.json()


class TestRouters:
    def test_mt_multi_select_reaches_the_backend_as_lists(self, auth_client, fake_manager):
        """Issue #107: request.POST.get() kept only the last selected connector."""
        calls = fake_manager('main.web.views.content.mtrouter', 'MTRouter')
        response = auth_client.post(reverse('web:mtrouter_view_manage'), {
            's': 'add', 'type': 'RandomRoundrobinMTRoute', 'order': '10', 'rate': '0.5',
            'smppconnectors': ['smpp1', 'smpp2'], 'filters': ['f1', 'f2'],
        }, **AJAX)
        assert response.status_code == 200
        data = calls[0][2]['data']
        assert data['smppconnectors'] == ['smpp1', 'smpp2'] and data['filters'] == ['f1', 'f2']

    def test_mo_multi_select_reaches_the_backend_as_lists(self, auth_client, fake_manager):
        calls = fake_manager('main.web.views.content.morouter', 'MORouter')
        auth_client.post(reverse('web:morouter_view_manage'), {
            's': 'add', 'type': 'FailoverMORoute', 'order': '5',
            'httpconnectors': ['h1', 'h2'], 'filters': ['f1'],
        }, **AJAX)
        data = calls[0][2]['data']
        assert data['httpconnectors'] == ['h1', 'h2'] and data['smppconnectors'] == [] and data['filters'] == ['f1']


CURRENT_USER = {
    'uid': 'u1', 'gid': 'g1', 'username': 'bob',
    'mt_messaging_cred': {
        'authorization': {'http_send': 'True', 'http_bulk': 'False', 'smpps_send': 'True'},
        'valuefilter': {'src_addr': '.*', 'priority': '^[0-3]$'},
        'defaultvalue': {'src_addr': 'None'},
        'quota': {'balance': '100.0', 'sms_count': 'ND'},
    },
}


class TestUserUpdates:
    def test_unchanged_form_sends_nothing(self):
        post = {'uid': 'u1', 'gid': 'g1', 'http_send': 'on', 'smpps_send': 'on', 'src_addr_f': '.*',
                'priority_f': '^[0-3]$', 'src_addr_d': '', 'balance': '100', 'sms_count': 'ND', 'password': ''}
        assert user_updates(post, CURRENT_USER) == []

    def test_unchecked_box_revokes_the_privilege(self):
        """An unchecked checkbox is absent from the POST; it used to default to True."""
        post = {'http_send': 'on'}
        assert ['mt_messaging_cred', 'authorization', 'smpps_send', 'False'] in user_updates(post, CURRENT_USER)

    def test_unlimited_quota_is_sent_as_none(self):
        assert user_updates({'http_send': 'on', 'smpps_send': 'on', 'balance': ''}, CURRENT_USER) == [
            ['mt_messaging_cred', 'quota', 'balance', 'None']]

    def test_changed_values(self):
        post = {'gid': 'g2', 'password': 'new', 'http_send': 'on', 'smpps_send': 'on', 'sms_count': '50'}
        assert user_updates(post, CURRENT_USER) == [
            ['gid', 'g2'], ['password', 'new'], ['mt_messaging_cred', 'quota', 'sms_count', '50']]

    def test_edit_view_skips_jcli_when_nothing_changed(self, auth_client, fake_manager):
        calls = fake_manager('main.web.views.content.users', 'Users', {'get_user': CURRENT_USER})
        response = auth_client.post(reverse('web:users_view_manage'), {
            's': 'edit', 'uid': 'u1', 'gid': 'g1', 'http_send': 'on', 'smpps_send': 'on',
        }, **AJAX)
        assert response.status_code == 200
        assert [c[0] for c in calls] == ['get_user']

    def test_password_update_is_mirrored_for_send_message(self, auth_client, fake_manager, stored_user):
        fake_manager('main.web.views.content.users', 'Users', {'get_user': CURRENT_USER})
        auth_client.post(reverse('web:users_view_manage'), {
            's': 'edit', 'uid': 'u1', 'password': 'fresh', 'http_send': 'on', 'smpps_send': 'on',
        }, **AJAX)
        assert UsersModel.objects.get(uid='u1').password == 'fresh'


class TestSmppConnectors:
    def test_edit_only_forwards_form_fields(self, auth_client, fake_manager):
        calls = fake_manager('main.web.views.content.smppccm', 'SMPPCCM')
        auth_client.post(reverse('web:smppccm_view_manage'), {
            's': 'edit', 'cid': 'c1', 'host': '10.0.0.1', 'port': '2775', 'csrfmiddlewaretoken': 'x',
        }, **AJAX)
        method, args, kwargs = calls[0]
        assert method == 'partial_update' and kwargs['cid'] == 'c1'
        assert kwargs['data'] == {'host': '10.0.0.1', 'port': '2775'}


class TestSendMessageUsers:
    def test_users_without_stored_password_are_flagged(self, auth_client, fake_manager, stored_user):
        fake_manager('main.web.views.content.send_message', 'Users', {'list_summary': {'users': [
            {'uid': 'u1', 'username': 'bob', 'status': 'enabled'},
            {'uid': 'u2', 'username': 'eve', 'status': 'enabled'},
        ]}})
        response = auth_client.post(reverse('web:send_message_view_manage'), {'s': 'list_users'}, **AJAX)
        flags = {u['uid']: u['has_password'] for u in response.json()['users']}
        assert flags == {'u1': True, 'u2': False}


class TestSubmitLogs:
    def test_unknown_date_column_is_ignored(self, auth_client):
        """The date column comes from the query string and used to reach the ORM unchecked."""
        url = reverse('web:submit_logs_view')
        response = auth_client.get(url, {'date_column': 'no_such_field', 'date_from': '2024-01-01'})
        assert response.status_code == 200
        assert response.context['date_column'] == 'created_at'


class TestApi:
    def test_users_list(self, auth_client, fake_manager):
        fake_manager('main.api.views.users', 'Users', {'list': {'users': [{'uid': 'u1'}]}})
        response = auth_client.get(reverse('api:users_list'))
        assert response.status_code == 200 and response.json() == {'users': [{'uid': 'u1'}]}

    def test_groups_create(self, auth_client, fake_manager):
        calls = fake_manager('main.api.views.groups', 'Groups', {'create': {'name': 'g1'}})
        response = auth_client.post(reverse('api:groups_list'), {'gid': 'g1'}, content_type='application/json')
        assert response.status_code == 201 and calls[0][0] == 'create'

    def test_errors_share_one_shape(self, auth_client, fake_manager):
        fake_manager('main.api.views.users', 'Users', {'retrieve': ObjectNotFoundError('Unknown user: nope')})
        response = auth_client.get(reverse('api:users_detail', args=['nope']))
        assert response.status_code == 404
        assert response.json()['error'] == 'Unknown user: nope'

    def test_gateway_down_is_a_503(self, auth_client, fake_manager):
        fake_manager('main.api.views.mtrouter', 'MTRouter', {'list': TelnetUnexpectedResponse('Jasmin is down')})
        response = auth_client.get(reverse('api:mtrouter_list'))
        assert response.status_code == 503 and response.json()['error'] == 'Jasmin is down'
