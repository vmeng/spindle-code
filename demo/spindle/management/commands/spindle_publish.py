from django.core.management.base import BaseCommand, CommandError
import spindle.publish

class Command(BaseCommand):
    help = 'Publish items and RSS feed'
    args = '[feed|all]'

    def handle(self, *args, **options):
        try:
            what = args[0]
        except KeyError:
            what = 'all'

        if what == 'feed':
            spindle.publish.publish_feed()
        elif what == 'all':
            spindle.publish.publish_all_items()
            spindle.publish.publish_feed()
        else:
            raise CommandError(u"Bad argument {}".format(what))

        self.stderr.write('Finished')
