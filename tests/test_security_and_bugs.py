"""
Regression tests for security hardening and critical bug fixes.
"""
import io

import pytest
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from main.core.exceptions import MissingKeyError, ValidationError
from main.core.models import Currency, EmailServer, SubmitLog, UsersModel
from main.core.smpp import Filters, MTRouter
from main.core.tasks.export_submit_logs import sanitize_spreadsheet_cell
from main.core.utils.cryptograph import FERNET_PREFIX
from main.users.forms import ChangePasswordForm, ProfileForm, ResetPasswordConfirmForm, ResetPasswordForm

User = get_user_model()
AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


@pytest.fixture
def staff_user(db):
    return User.objects.create_superuser(
        username='sec_admin',
        email='sec_admin@example.com',
        password='StrongPassword123!',
    )


@pytest.fixture
def regular_user(db):
    user = User.objects.create_user(
        username='regular_user',
        email='regular@example.com',
        password='StrongPassword123!',
        is_staff=False,
        is_superuser=False,
    )
    user.is_email = True
    user.is_verified = True
    user.save()
    return user


@pytest.mark.django_db
class TestRBACAuthorization:
    def test_non_staff_blocked_from_rest_api(self, client, regular_user):
        client.force_login(regular_user)
        assert client.get(reverse('api:api_root')).status_code == 403
        assert client.get(reverse('api:users_list')).status_code == 403
        assert client.post(reverse('api:mtrouter_flush')).status_code == 403

    def test_non_staff_blocked_from_gateway_web_pages(self, client, regular_user):
        client.force_login(regular_user)
        for name in ('web:dashboard_view', 'web:users_view', 'web:filters_view', 'web:submit_logs_view'):
            assert client.get(reverse(name)).status_code == 403

    def test_non_staff_blocked_from_ajax_manage_endpoints(self, client, regular_user):
        client.force_login(regular_user)
        response = client.post(reverse('web:groups_view_manage'), {'s': 'list'}, **AJAX)
        assert response.status_code == 403
        assert response.json()['status'] == 403


@pytest.mark.django_db
class TestAuthSecurity:
    def test_open_redirect_blocked_on_signin(self, client, staff_user):
        response = client.post(
            reverse('users:signin_view'),
            {'username': staff_user.username, 'password': 'StrongPassword123!', 'next': 'https://evil.example.com/phish'},
        )
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_relative_next_url_allowed_on_signin(self, client, staff_user):
        response = client.post(
            reverse('users:signin_view'),
            {'username': staff_user.username, 'password': 'StrongPassword123!', 'next': '/users/'},
        )
        assert response.status_code == 302
        assert response['Location'] == '/users/'

    def test_logout_rejects_get_and_accepts_post(self, client, staff_user):
        client.force_login(staff_user)
        assert client.get(reverse('users:logout_view')).status_code == 405
        assert client.post(reverse('users:logout_view')).status_code == 302

    def test_password_reset_does_not_enumerate_users(self, client):
        resp_missing = client.post(reverse('users:reset_view'), {'username': 'nobody@example.com'})
        assert resp_missing.status_code == 302


@pytest.mark.django_db
class TestFormsAndAvatar:
    def test_forms_have_widget_attrs_and_proper_clean(self):
        pw_form = ChangePasswordForm()
        assert pw_form.fields['password1'].widget.attrs.get('class') == 'form-control'
        assert ResetPasswordForm().fields['username'].widget.attrs.get('class') == 'form-control'

        reset_form = ResetPasswordConfirmForm(data={'password': 'StrongPassword123!', 'password2': 'StrongPassword123!'})
        assert reset_form.is_valid()
        assert isinstance(reset_form.cleaned_data, dict)

        weak_form = ChangePasswordForm(data={'password': 'old', 'password1': '12345', 'password2': '12345'})
        assert not weak_form.is_valid()

        short_email_form = ProfileForm(data={'first_name': 'Al', 'last_name': 'Bo', 'email': 'a@b.io'})
        assert short_email_form.is_valid()

    def test_avatar_upload_works_with_pillow_12_and_rejects_non_images(self, client, staff_user, tmp_path, settings):
        settings.MEDIA_ROOT = str(tmp_path)
        client.force_login(staff_user)

        buf = io.BytesIO()
        Image.new('RGB', (100, 100), color='blue').save(buf, format='PNG')
        buf.seek(0)
        upload = SimpleUploadedFile('avatar.png', buf.read(), content_type='image/png')
        resp = client.post(
            reverse('users:profile_view'),
            {'s': 'avatar', 'avatar_file': upload, 'avatar_data': '{"x":0,"y":0,"w":80,"h":80}'},
        )
        assert resp.status_code == 200
        assert resp.json()['state'] == 200

        bad = SimpleUploadedFile('evil.svg', b'<svg onload=alert(1)></svg>', content_type='image/svg+xml')
        resp_bad = client.post(reverse('users:profile_view'), {'s': 'avatar', 'avatar_file': bad})
        assert resp_bad.status_code == 400


@pytest.mark.django_db
class TestModelsAndMigrations:
    def test_submit_log_accepts_long_esme_status(self):
        log = SubmitLog.objects.create(
            msgid='msg-fail-001',
            destination_addr='15550001111',
            status='ESME_RDELIVERYFAILURE',
            uid='u1',
            created_at=timezone.now(),
            status_at=timezone.now(),
        )
        assert log.status == 'ESME_RDELIVERYFAILURE'

    def test_email_server_password_is_encrypted_at_rest(self):
        srv = EmailServer.objects.create(
            server='smtp.example.com',
            port=587,
            username='alerts@example.com',
            password='super-secret-smtp-password',
            ssl=False,
            active=False,
        )
        with connection.cursor() as cursor:
            cursor.execute('SELECT password FROM core_emailserver WHERE id = %s', [srv.pk])
            raw = cursor.fetchone()[0]
        assert raw.startswith(FERNET_PREFIX)
        assert EmailServer.objects.get(pk=srv.pk).password == 'super-secret-smtp-password'

    def test_samples_command_is_idempotent_and_never_recreates_admin(self, staff_user):
        # Database already has staff_user (not named 'admin'): samples must NOT recreate admin/secret
        call_command('samples')
        call_command('samples')
        assert not User.objects.filter(username='admin').exists()
        assert Currency.objects.filter(code='USD').count() == 0
        assert Currency.objects.filter(code='US').count() == 1


@pytest.mark.django_db
class TestExportSecurity:
    def test_formula_injection_sanitization(self):
        assert sanitize_spreadsheet_cell('=CMD|"/C calc"!A0') == '\'=CMD|"/C calc"!A0'
        assert sanitize_spreadsheet_cell('+12345') == "'+12345"
        assert sanitize_spreadsheet_cell('-1+1') == "'-1+1"
        assert sanitize_spreadsheet_cell('@SUM(A1:A2)') == "'@SUM(A1:A2)"
        assert sanitize_spreadsheet_cell('Hello world') == 'Hello world'

    def test_export_download_blocks_other_users(self, client, staff_user, settings):
        settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
        other_admin = User.objects.create_superuser(
            username='other_admin', email='other@example.com', password='StrongPassword123!'
        )
        task_id = 'test-task-idor'
        cache.set(f'export_file_{task_id}', {
            'content': 'a,b\n1,2\n',
            'content_type': 'text/csv',
            'filename': 'logs.csv',
            'owner_id': staff_user.id,
        }, 300)
        cache.set(f'export_progress_{task_id}', {'status': 'completed', 'progress': 100, 'owner_id': staff_user.id}, 300)

        client.force_login(other_admin)
        assert client.get(reverse('web:submit_logs_export_progress', args=[task_id])).status_code == 403
        assert client.get(reverse('web:submit_logs_export_download', args=[task_id])).status_code == 403

        client.force_login(staff_user)
        assert client.get(reverse('web:submit_logs_export_download', args=[task_id])).status_code == 200


@pytest.mark.django_db
class TestGatewayHardening:
    def test_evalpy_filter_blocked_by_default(self):
        f = Filters.__new__(Filters)
        with pytest.raises(ValidationError, match='EvalPyFilter is disabled'):
            f.create({'type': 'EvalPyFilter', 'fid': 'f_rce', 'parameter': 'routable'})

    def test_mtrouter_rejects_nan_and_inf_rates(self):
        m = MTRouter.__new__(MTRouter)
        for bad_rate in ('nan', 'inf', '-inf'):
            with pytest.raises(MissingKeyError):
                m.create({'type': 'DefaultRoute', 'rate': bad_rate, 'smppconnectors': ['c1']})

    def test_smppccm_api_masks_passwords(self, client, staff_user, monkeypatch):
        class FakeSMPP:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def list(self):
                return {'connectors': [{'cid': 'c1', 'password': 'carrier-secret-pw'}]}

            def retrieve(self, cid):
                return {'connector': {'cid': cid, 'password': 'carrier-secret-pw'}}

        monkeypatch.setattr('main.api.views.smppccm.SMPPCCM', FakeSMPP)
        client.force_login(staff_user)
        resp_list = client.get(reverse('api:smppccm_list'))
        assert resp_list.status_code == 200
        assert resp_list.json()['connectors'][0]['password'] == '********'

        resp_detail = client.get(reverse('api:smppccm_detail', args=['c1']))
        assert resp_detail.status_code == 200
        assert resp_detail.json()['connector']['password'] == '********'

    def test_user_password_edit_syncs_for_preexisting_jcli_user(self, client, staff_user, monkeypatch):
        class FakeUsers:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get_user(self, uid):
                return {'uid': uid, 'gid': 'g_existing', 'username': 'alice', 'mt_messaging_cred': {}}

            def partial_update(self, updates, uid):
                return {'user': {'uid': uid}}

        monkeypatch.setattr('main.web.views.content.users.Users', FakeUsers)
        client.force_login(staff_user)
        resp = client.post(
            reverse('web:users_view_manage'),
            {'s': 'edit', 'uid': 'u_preexisting', 'password': 'new-jcli-password'},
            **AJAX,
        )
        assert resp.status_code == 200
        assert UsersModel.objects.get(uid='u_preexisting').password == 'new-jcli-password'
