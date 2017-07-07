from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django_otp import devices_for_user
from django.utils import timezone
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Ensures there exists a user named "admin" with the password "rattic"'

    def handle(self, *args, **options):
        # Create an admin user or find one if it exists
        try:
            u = User.objects.get(username='admin')
        except ObjectDoesNotExist:
            u = User(username='admin', email='admin@example.com')

        # (Re)set the password to rattic
        u.set_password('rattic')

        # Make them a staff member
        u.is_staff = True

	# Create private group and assign it to the user
	group = Group(name='private_admin', created=timezone.now())
	group.save()
	u.self_group = group

        # Save the user
        u.save()

	u.groups.add(group)
	u.save()

        # Delete any tokens they may have
        for dev in devices_for_user(u):
            dev.delete()
