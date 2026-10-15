"""
Jasmin user passwords are kept so Send SMS can bind as the user: they are stored encrypted.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from main.core.models import GroupsModel, UsersModel
from main.core.utils.cryptograph import decrypt_text, encrypt_text


class TestCryptograph:
    def test_round_trip(self):
        token = encrypt_text('s3cret')
        assert token != 's3cret' and token.startswith('gAAAAA')
        assert decrypt_text(token) == 's3cret'

    def test_plain_text_from_before_encryption_is_returned_as_is(self):
        assert decrypt_text('legacy-password') == 'legacy-password'

    def test_token_from_another_key_is_not_handed_out(self, settings):
        token = encrypt_text('s3cret')
        settings.FIELD_ENCRYPTION_KEY = 'a-different-key'
        assert decrypt_text(token) == ''

    def test_dedicated_key_survives_secret_key_rotation(self, settings):
        settings.FIELD_ENCRYPTION_KEY = 'stable-key'
        token = encrypt_text('s3cret')
        settings.SECRET_KEY = 'rotated-secret-key'
        assert decrypt_text(token) == 's3cret'


@pytest.mark.django_db
class TestEncryptedField:
    def test_password_is_encrypted_in_the_database(self):
        owner = get_user_model().objects.create(username='owner', email='owner@example.com')
        UsersModel.objects.create(uid='u1', gid=GroupsModel.objects.create(gid='g1'), username='bob',
                                  password='s3cret', parameters='', user=owner)
        with connection.cursor() as cursor:
            cursor.execute('SELECT password FROM tbl_users')
            stored = cursor.fetchone()[0]
        assert stored.startswith('gAAAAA') and 's3cret' not in stored
        assert UsersModel.objects.get(uid='u1').password == 's3cret'

    def test_queryset_update_is_encrypted_too(self):
        owner = get_user_model().objects.create(username='owner', email='owner@example.com')
        UsersModel.objects.create(uid='u1', gid=GroupsModel.objects.create(gid='g1'), username='bob',
                                  password='old', parameters='', user=owner)
        UsersModel.objects.filter(uid='u1').update(password='new')
        with connection.cursor() as cursor:
            cursor.execute('SELECT password FROM tbl_users')
            assert cursor.fetchone()[0].startswith('gAAAAA')
        assert UsersModel.objects.get(uid='u1').password == 'new'
