from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import logging

from spindle.publish import publish_item, publish_feed, \
    publish_exports_feed, publish_all_items
from spindle.models import Item


class Command(BaseCommand):
    help = 'Publish items and RSS feed'
    args = '[keywords | exports | all | <item id>]'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Only process ten items, for debugging purposes.'),
        )

    def handle(self, what='all', *args, **options):
        verbosity = int(options['verbosity'])
        debug = options['debug']

        self.setup_logging(verbosity)

        if debug:
            self.stderr.write("** Running in debug mode: only 10 items will be processed **\n")

        if what == 'keywords':
            publish_feed(debug=debug)
        elif what == 'exports':
            publish_exports_feed(debug=debug)
        elif what == 'all':
            publish_all_items(debug=debug)
            publish_feed(debug=debug)
        elif what.isdigit():
            item_id = int(what)
            item = Item.objects.get(pk=item_id)
            self.stderr.write('Publishing item {}, "{}"\n'.format(item_id, item.name))
            publish_item(item)
        else:
            raise CommandError(u"Bad argument {}".format(what))

    def setup_logging(self, verbosity):
        logger = logging.getLogger('spindle.publish')
        logger.addHandler(logging.StreamHandler(stream=self.stderr))

        if verbosity >= 2:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
