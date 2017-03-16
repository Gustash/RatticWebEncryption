from django.core.management import BaseCommand
from request.Mailing import mail_manager

class Command(BaseCommand):
	def handle(self, *args, **options):
		mail_manager.update()
