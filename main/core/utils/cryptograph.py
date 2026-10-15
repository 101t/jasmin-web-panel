# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import base64
import hashlib
import logging

from django.conf import settings

__all__ = ['md5', 'sha1', 'sha256', 'sha512', 'encrypt_text', 'decrypt_text']

logger = logging.getLogger(__name__)

# Every Fernet token starts with these characters (version byte 0x80, then the timestamp).
FERNET_PREFIX = 'gAAAAA'


def md5(data):
    data_hash = hashlib.md5()
    data_hash.update(str(data).encode('utf-8'))
    return str(data_hash.hexdigest())

def sha1(data):
    data_hash = hashlib.sha1()
    data_hash.update(str(data).encode('utf-8'))
    return str(data_hash.hexdigest())

def sha256(data):
    data_hash = hashlib.sha256()
    data_hash.update(str(data).encode('utf-8'))
    return str(data_hash.hexdigest())

def sha512(data):
    data_hash = hashlib.sha512()
    data_hash.update(str(data).encode('utf-8'))
    return str(data_hash.hexdigest())


def _fernet():
    from cryptography.fernet import Fernet
    # FIELD_ENCRYPTION_KEY lets SECRET_KEY be rotated without losing the stored secrets.
    secret = getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or settings.SECRET_KEY
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode('utf-8')).digest()))


def encrypt_text(value):
    """Encrypt a secret that must be readable again (e.g. a password the panel sends to Jasmin)."""
    return _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def decrypt_text(value):
    """Decrypt ``encrypt_text`` output.

    Values stored before encryption existed are returned unchanged. A token that cannot be
    decrypted (the key changed) gives '' rather than handing the ciphertext out as a password.
    """
    if not value.startswith(FERNET_PREFIX):
        return value
    from cryptography.fernet import InvalidToken
    try:
        return _fernet().decrypt(value.encode('ascii')).decode('utf-8')
    except InvalidToken:
        logger.warning('Cannot decrypt a stored secret: SECRET_KEY or FIELD_ENCRYPTION_KEY changed')
        return ''
