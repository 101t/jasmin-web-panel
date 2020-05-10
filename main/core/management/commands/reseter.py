import glob, os

from django.core.management import BaseCommand

class Command(BaseCommand):
	help = "Removes all migrations"
	app_directory = "main"

	def handle(self, *args, **options):
		try:
			for filename in glob.iglob("{0}/**/migrations/*.py".format(self.app_directory)):
				if filename.split("/")[-1] != "__init__.py":
					os.remove(filename)
			print("Migration files removed.")
		except OSError:
			print("Migration files may not exist.")