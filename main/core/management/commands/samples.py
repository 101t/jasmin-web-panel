from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings

from main.users.models import User
from main.core.models import Currency, EmailServer


class Command(BaseCommand):
	help = "Add default data to database"
	def handle(self, *args, **options):
		call_command("migrate")
		EmailServer.objects.get_or_create(
			server="mail.example.com",
			port=587,
			username="info@example.com",
			password="123456",
			ssl=False,
			active=False,
		)
		self.stdout.write("Default Email Server Added")
		user1, created = User.objects.get_or_create(pk=1)
		if created:
			user1.username = "admin"
			user1.first_name = "Chris"
			user1.last_name = "Daughtry"
			user1.email = "admin@example.com"
			user1.set_password("secret")
			user1.is_active = True
			user1.is_staff = True
			user1.is_superuser = True
			user1.is_email = True
			user1.is_verified = True
			user1.save()
			self.stdout.write("Default User Added")
		currencies = [
			Currency(
				name="Turkish Lira",
				code="TL",
				code3="TRY",
				symbol="₺",
				order=1,
			),
			Currency(
				name="United State Dollar",
				code="US",
				code3="USD",
				symbol="$",
				order=2,
			),
			Currency(
				name="Euro",
				code="EU",
				code3="EUR",
				symbol="€",
				order=3,
			),
		]
		Currency.objects.bulk_create(currencies)
		self.stdout.write("Default Currencies Added")