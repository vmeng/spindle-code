from django.core.management.base import NoArgsCommand, CommandError
import logging
import spindle.tasks

logger = logging.getLogger('spindle.tasks')

class Command(NoArgsCommand):
    help = 'Scrape the RSS feed for new items'

    def handle_noargs(self, *args, **options):
        verbosity = int(options['verbosity'])
        self.setup_logging(verbosity)

        spindle.tasks.scrape()        
        self.stdout.write('Finished scraping')

    def setup_logging(self, verbosity):
        logger.addHandler(logging.StreamHandler(stream=self.stderr))

        if verbosity >= 2:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
