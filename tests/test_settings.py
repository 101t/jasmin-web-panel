"""
Settings are read from the environment once, at import: check them in a fresh interpreter.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_django(code, **env):
    """Run ``code`` with Django set up from ``env``; return what it prints as JSON."""
    environment = {k: v for k, v in os.environ.items() if k not in ('DEBUG', 'HTTPS_ONLY', 'SUBMIT_LOG')}
    environment.update({'SECRET_KEY': 'settings-test-key', 'PRODB_URL': 'sqlite:///:memory:',
                        'DEVDB_URL': 'sqlite:///:memory:', 'PYTHONWARNINGS': 'ignore'}, **env)
    script = 'import django, json; django.setup()\n' + code
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=environment,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize('value, expected', [
    ('False', False), ('0', False), ('no', False), ('', False), ('True', True), ('1', True),
])
def test_debug_flag_is_parsed_as_a_boolean(value, expected):
    """bool("False") is True: DEBUG=False in .env (or DEBUG: 0 in compose) used to enable debug mode."""
    flags = run_django(
        'from django.conf import settings; print(json.dumps([settings.DEBUG, settings.SUBMIT_LOG]))',
        DJANGO_SETTINGS_MODULE='config.settings.dev', DEBUG=value, SUBMIT_LOG=value)
    assert flags == [expected, expected]


def test_https_only_redirects_pages_but_not_the_health_check():
    statuses = run_django(
        'from django.core.management import call_command; call_command("migrate", verbosity=0)\n'
        'from django.test import Client, override_settings; from django.test.utils import setup_test_environment\n'
        'setup_test_environment(); c = Client()\n'
        'with override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}):\n'
        '    print(json.dumps([c.get("/account/login/").status_code, c.get("/api/health_check").status_code]))',
        DJANGO_SETTINGS_MODULE='config.settings.pro', HTTPS_ONLY='True', ALLOWED_HOSTS='testserver')
    assert statuses == [301, 200]
