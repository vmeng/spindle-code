from django.core.management.base import NoArgsCommand, CommandError
import spindle.tasks

class Command(NoArgsCommand):
    help = 'Scrape the RSS feed for new items'

    def handle_noargs(self, *args, **options):
        spindle.tasks.scrape()        
        self.stdout.write('Finished scraping')
