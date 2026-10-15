"""
The release workflow publishes the image tagged with config/version.py: everything that names
a version must agree, or users would pull an image that does not match the code they read.
"""
import os
import re
import tomllib

from config.version import VERSION

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


def test_pyproject_version_matches():
    assert tomllib.loads(read('pyproject.toml'))['project']['version'] == VERSION


def test_compose_uses_the_released_image():
    tags = re.findall(r'image: tarekaec/jasmin_web_panel:(\S+)', read('docker-compose.yml'))
    assert tags and set(tags) == {VERSION}


def test_changelog_has_a_section_for_this_version():
    assert re.search(r'^## %s\b' % re.escape(VERSION), read('CHANGELOG.md'), re.MULTILINE)
