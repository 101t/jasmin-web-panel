from django.db import models

from main.core.utils.cryptograph import decrypt_text, encrypt_text


class EncryptedCharField(models.CharField):
    """A CharField stored encrypted (Fernet) and read back as plain text.

    For secrets the panel must use again, such as the Jasmin user passwords Send SMS binds
    with. Values saved before this field existed are read as-is and encrypted on next save.
    Encryption is not deterministic, so filtering on the field does not match.
    """

    def from_db_value(self, value, expression, connection):
        return decrypt_text(value) if value else value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_text(value) if value else value
