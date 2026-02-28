"""
Tests for web views (dashboard, submit_logs).
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        username='testadmin',
        email='testadmin@example.com',
        password='testpass123',
        is_active=True,
        is_staff=True,
    )
    return user


@pytest.fixture
def auth_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.mark.django_db
class TestDashboardView:
    def test_redirect_unauthenticated(self, client):
        url = reverse('web:dashboard_view')
        response = client.get(url)
        assert response.status_code == 302
        assert '/account/login/' in response['Location']

    def test_dashboard_authenticated(self, auth_client):
        url = reverse('web:dashboard_view')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_dashboard_uses_correct_template(self, auth_client):
        url = reverse('web:dashboard_view')
        response = auth_client.get(url)
        assert 'web/dashboard.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestSubmitLogsView:
    def test_redirect_unauthenticated(self, client):
        url = reverse('web:submit_logs_view')
        response = client.get(url)
        assert response.status_code == 302

    def test_submit_logs_authenticated(self, auth_client):
        url = reverse('web:submit_logs_view')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_submit_logs_search_param(self, auth_client):
        url = reverse('web:submit_logs_view')
        response = auth_client.get(url, {'search': 'test-msg'})
        assert response.status_code == 200

    def test_submit_logs_status_filter(self, auth_client):
        url = reverse('web:submit_logs_view')
        for status_filter in ['success', 'fail', 'unknown', '']:
            response = auth_client.get(url, {'status_filter': status_filter})
            assert response.status_code == 200


@pytest.mark.django_db
class TestGlobalManageView:
    def test_gateway_state_check(self, auth_client):
        url = reverse('web:global_manage')
        response = auth_client.get(
            url,
            {'s': 'gw_state'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_USER_AGENT='Mozilla/5.0 TestAgent',
        )
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
