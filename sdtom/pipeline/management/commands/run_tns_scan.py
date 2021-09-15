from django.core.management.base import BaseCommand

from sdtom.pipeline.jobs import find_new_tns_classifications


class Command(BaseCommand):
    help = 'Searches for new TNS classifications for exisitng targets'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Starting scan...')
            find_new_tns_classifications()
            self.stdout.write('Done.')
        except KeyboardInterrupt:
            self.stdout.write('Exiting...')
