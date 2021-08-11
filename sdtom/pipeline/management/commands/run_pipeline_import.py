from django.core.management.base import BaseCommand

from sdtom.pipeline.jobs import fetch_new_lasair_alerts


class Command(BaseCommand):
    help = 'Runs the target import pipeline'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Starting import...')
            fetch_new_lasair_alerts()
            self.stdout.write('Done.')
        except KeyboardInterrupt:
            self.stdout.write('Exiting...')
