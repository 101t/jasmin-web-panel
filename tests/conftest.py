"""
Pytest configuration and fixtures for the test suite.
"""
import pytest
# Override settings for all tests to avoid requiring external services
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Disable DRF throttling during tests to avoid cache dependency
TEST_REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # Throttling disabled in tests
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}


@pytest.fixture(autouse=True)
def use_local_memory_cache(settings):
    """Override cache to use LocMemCache for all tests (no Redis required)."""
    settings.CACHES = TEST_CACHES
    settings.REST_FRAMEWORK = TEST_REST_FRAMEWORK
