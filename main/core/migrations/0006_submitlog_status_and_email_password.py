from django.db import migrations, models

import main.core.models.fields
from main.core.utils.cryptograph import FERNET_PREFIX, encrypt_text


def encrypt_existing_email_passwords(apps, schema_editor):
    EmailServer = apps.get_model("core", "EmailServer")
    for server in EmailServer.objects.all():
        if server.password and not server.password.startswith(FERNET_PREFIX):
            EmailServer.objects.filter(pk=server.pk).update(password=encrypt_text(server.password))


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_encrypt_user_passwords"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submitlog",
            name="status",
            field=models.CharField(db_index=True, max_length=50, verbose_name="Status"),
        ),
        migrations.AlterField(
            model_name="emailserver",
            name="password",
            field=main.core.models.fields.EncryptedCharField(max_length=255, verbose_name="Password"),
        ),
        migrations.RunPython(encrypt_existing_email_passwords, migrations.RunPython.noop),
    ]
