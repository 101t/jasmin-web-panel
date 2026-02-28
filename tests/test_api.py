"""
Tests for the REST API health check endpoint.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestHealthCheckEndpoint:
    def test_health_check_no_auth_required(self, client):
        """Health check should be accessible without authentication."""
        url = reverse('api:health_check')
        response = client.get(url)
        assert response.status_code == 200

    def test_health_check_response_format(self, client):
        url = reverse('api:health_check')
        response = client.get(url)
        data = response.json()
        assert 'version' in data
        assert 'status' in data
        assert data['status'] == 'ok'

    def test_health_check_version(self, client):
        from config.version import VERSION
        url = reverse('api:health_check')
        response = client.get(url)
        data = response.json()
        assert data['version'] == VERSION


@pytest.mark.django_db
class TestApiRootEndpoint:
    def test_api_root_requires_auth(self, client):
        """API root should require authentication."""
        url = reverse('api:api_root')
        response = client.get(url)
        # Should return 403 (forbidden) or 401 (unauthorized)
        assert response.status_code in (401, 403)

    def test_api_root_authenticated(self, client, django_user_model):
        user = django_user_model.objects.create_superuser(
            username='apiuser',
            email='apiuser@example.com',
            password='apipass123',
            is_active=True,
            is_staff=True,
        )
        client.force_login(user)
        url = reverse('api:api_root')
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert 'groups' in data
        assert 'users' in data
        assert 'health_check' in data
