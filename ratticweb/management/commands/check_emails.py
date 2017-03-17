from django.core.management import BaseCommand
from request.mailing import MailManager

class Command(BaseCommand):
	def handle(self, *args, **options):
		MailManager.update()
