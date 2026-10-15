from django.db import migrations

import main.core.models.fields


def encrypt_passwords(apps, schema_editor):
    """Re-save every stored password: the new field encrypts it on the way in."""
    UsersModel = apps.get_model('core', 'UsersModel')
    for user in UsersModel.objects.exclude(password=''):
        UsersModel.objects.filter(pk=user.pk).update(password=user.password)


def decrypt_passwords(apps, schema_editor):
    """Write the passwords back as plain text before the column returns to a plain CharField."""
    UsersModel = apps.get_model('core', 'UsersModel')
    with schema_editor.connection.cursor() as cursor:
        for user in UsersModel.objects.all():
            cursor.execute('UPDATE tbl_users SET password = %s WHERE id = %s', [user.password, user.pk])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_submitlog_charge_alter_moroutersmodel_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersmodel',
            name='password',
            field=main.core.models.fields.EncryptedCharField(max_length=255, verbose_name='Password'),
        ),
        migrations.RunPython(encrypt_passwords, decrypt_passwords),
    ]
