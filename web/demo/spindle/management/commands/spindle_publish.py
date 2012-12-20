from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import logging

from spindle.publish import publish_item, publish_exports_feed, publish_fulltext_feed, publish_all_items
from spindle.models import Item


class Command(BaseCommand):
    help = """Publish items and RSS feed.
    
    With argument "exports", writes out exported file formats
    (plaintext/HTML/VTT) for all tracks that are marked for export and
    whose associated files are missing or out of date.  See the
    settings SPINDLE_PUBLIC_URL and SPINDLE_PUBLIC_DIRECTORY for the
    location of these files.

    With argument "rss", publishes an RSS feed of all existing export
    files. See setting SPINDLE_EXPORTS_RSS_FILENAME to customize the
    URL of this feed.

    With argument "fulltext", publishes an RSS feed containing the
    full plain text of all exported transcripts. See setting
    SPINDLE_FULLTEXT_RSS_FILENAME.

    With argument "all", does all of the above in order. This is also the
    default if no argument is supplied.

    Otherwise, the argument should be the numeric ID of an item whose
    transcript tracks will be exported.
    """
    args = 'rss | exports | fulltext | all | <item id>'
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

        if what == 'rss':
            publish_exports_feed(debug=debug)
        elif what == 'exports':
            publish_all_items(debug=debug)
        elif what == 'fulltext':
            publish_fulltext_feed(debug=debug)
        elif what == 'all':
            publish_all_items(debug=debug)
            publish_exports_feed(debug=debug)
            publish_fulltext_feed(debug=debug)
        elif what.isdigit():
            item_id = int(what)
            item = Item.objects.get(pk=item_id)
            self.stderr.write(u'Publishing item {}, "{}"\n'.format(item_id, item.name))
            publish_item(item)
        else:
            raise CommandError(u"Bad argument {}. Supply one of: {}".format(what, Command.args))

    def setup_logging(self, verbosity):
        logger = logging.getLogger('spindle')
        logger.addHandler(logging.StreamHandler(stream=self.stderr))

        if verbosity >= 2:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
