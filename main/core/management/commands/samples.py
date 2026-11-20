from django.core.management.base import BaseCommand
from django.core.management import call_command

from main.users.models import User
from main.core.models import Currency, EmailServer


class Command(BaseCommand):
    help = "Add default data to database (idempotent)"

    def handle(self, *args, **options):
        call_command("migrate")
        if not EmailServer.objects.exists():
            EmailServer.objects.create(
                server="mail.example.com",
                port=587,
                username="info@example.com",
                password="123456",
                ssl=False,
                active=False,
            )
            self.stdout.write("Default Email Server Added")

        # Only bootstrap the default admin account on a brand-new database.
        # If an administrator has deleted or renamed admin, restarting the container
        # must never recreate admin/secret.
        if not User.objects.exists():
            user1 = User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="secret",
                first_name="Chris",
                last_name="Daughtry",
            )
            user1.is_email = True
            user1.is_verified = True
            user1.save(update_fields=["is_email", "is_verified"])
            self.stdout.write("Default User Added")

        default_currencies = [
            dict(name="Turkish Lira", code="TL", code3="TRY", symbol="₺", order=1),
            dict(name="United State Dollar", code="US", code3="USD", symbol="$", order=2),
            dict(name="Euro", code="EU", code3="EUR", symbol="€", order=3),
        ]
        created_any = False
        for item in default_currencies:
            _, created = Currency.objects.get_or_create(code=item["code"], defaults=item)
            created_any = created_any or created
        if created_any:
            self.stdout.write("Default Currencies Added")
