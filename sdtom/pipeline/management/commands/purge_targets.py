from django.core.management.base import BaseCommand
from tom_targets.models import Target
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Purge old uninteresting targets'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Removing targets...')
            Target.objects.filter(
                targetlist__name='Uninteresting', created__lt=timezone.now() - timedelta(days=30)
            ).delete()
            self.stdout.write('Done.')
        except KeyboardInterrupt:
            self.stdout.write('Exiting...')
