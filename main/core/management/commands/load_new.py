from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from main.users.models import User
from main.core.models import Currency, EmailServer


class Command(BaseCommand):
	help = "This command to load default domain and subdomains samples into database"
	def add_arguments(self, parser):
		parser.add_argument("--add", action="store_true", dest="add", default=True, help="add default domain only")
	def handle(self, *args, **options):
		if options["add"]:
			emailserver, created = EmailServer.objects.get_or_create(
				server="mail.example.com",
				port=587,
				username="info@example.com",
				password="123456",
				ssl=False,
				active=True,
			)
			print("Default Email Server Added")
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
				print("Default User Added")
			obj1, created = Currency.objects.get_or_create(
				name="Turkish Lira",
				code="TL",
				code3="TRY",
				symbol="₺",
				order=1,
			)
			if created:
				print("Default Currency1 Added")
			obj2, created = Currency.objects.get_or_create(
				name="United State Dollar",
				code="US",
				code3="USD",
				symbol="$",
				order=2,
			)
			if created:
				print("Default Currency2 Added")
			obj3, created = Currency.objects.get_or_create(
				name="Euro",
				code="EU",
				code3="EUR",
				symbol="€",
				order=3,
			)
			if created:
				print("Default Currency3 Added")