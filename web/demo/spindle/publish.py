"""Publish Spindle transcripts and RSS as static files."""

import os
import urlparse
import logging
from collections import namedtuple

from django.conf import settings
from django.utils.feedgenerator import Rss201rev2Feed

from spindle.models import Item, PUBLISH_STATES
from spindle.keywords.keywords import keywords_and_ngrams
import spindle.utils
from spindle.single_instance_task import single_instance_task

logger = logging.getLogger(__name__)

# Temporary namespace for our special-purpose RSS URIs
RSS_SCHEME_ROOT = 'http://rss.oucs.ox.ac.uk/spindle/'

# RSS namespaces to use
RSS_NAMESPACES = {
    'atom': "http://www.w3.org/2005/Atom",
    'creativeCommons': "http://backend.userland.com/creativeCommonsRssModule",
    'dc': "http://purl.org/dc/elements/1.1/",
    'ev': "http://purl.org/rss/1.0/modules/event/",
    'geo': "http://www.w3.org/2003/01/geo/wgs84_pos#",
    'itunes': "http://www.itunes.com/dtds/podcast-1.0.dtd",
    'itunesu': "http://www.itunesu.com/feed",
    'media': "http://search.yahoo.com/mrss/",
    's': "http://purl.org/steeple",
    'spindle': RSS_SCHEME_ROOT
    }

# 'scheme' attributes for RSS <category> tags
RSS_VISIBILITY_SCHEME = 'http://rss.oucs.ox.ac.uk/itunesu_support'

# 'rel' attributes for <atom:link> tags
RSS_TRANSCRIPT_REL = RSS_SCHEME_ROOT + 'transcript/'
RSS_CAPTIONS_REL = RSS_SCHEME_ROOT + 'captions/'

# Public URL for published items, making sure it ends with a slash
PUBLIC_URL = settings.SPINDLE_PUBLIC_URL
if not PUBLIC_URL.endswith('/'): PUBLIC_URL += '/'

# Filenames for published RSS feeds
KEYWORDS_RSS_FILENAME = os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY,
                            settings.SPINDLE_KEYWORDS_RSS_FILENAME)
EXPORTS_RSS_FILENAME = os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY,
                                    settings.SPINDLE_EXPORTS_RSS_FILENAME)

# URLs for published RSS feeds
KEYWORDS_RSS_URL = urlparse.urljoin(PUBLIC_URL, settings.SPINDLE_KEYWORDS_RSS_FILENAME)
EXPORTS_RSS_URL = urlparse.urljoin(PUBLIC_URL,
                                   settings.SPINDLE_EXPORTS_RSS_FILENAME)

# How significant keywords have to be
try:
    LL_THRESHOLD = settings.SPINDLE_KEYWORD_LL_THRESHOLD
except:
    LL_THRESHOLD = 40
    
# A description of one type of exported transcript to publish: HTML,
# Text, SRT, etc.
ExportType = namedtuple('ExportType', (
    # name of the field in the Track model that
    # controls whether this type of file should
    # be exported:
    'visibility_field',
    
    'extension', 
    'description', 
    'mime_type',
    
    # string to use in the <link> tag in
    # exported RSS:
    'rel',
    
    # Track model method that writes this type
    # of file:
    'write_method'))

# The types of exports
EXPORT_TYPES = (
    ExportType('publish_text', '.txt', 'Plain text transcript',
               'text/plain',
               RSS_TRANSCRIPT_REL, 'write_plaintext'),
    ExportType('publish_vtt', '.vtt', 'WebVTT captions',
               'text/vtt', 
               RSS_CAPTIONS_REL, 'write_vtt'),
    ExportType('publish_transcript', '.html', 'HTML transcript', 
               'text/html',
               RSS_TRANSCRIPT_REL, 'write_html'))

# Record type describing a transcript to publish for a particular item.
Export = namedtuple('ItemExport',
                    ['href', 
                     
                     # Absolute filesystem path
                     'path', 

                     # RSS attributes
                     'lang', 'rel', 'mime_type', 'description',
                     
                     'visibility',

                     # Method which writes this export to a provided
                     # file: actually an alias for the bound method of
                     # the associated Track object
                     'write',

                     # The Track object itself
                     'track'])


# 
# Export transcripts to disk in different formats
#

@single_instance_task(name='spindle.publish.all_items',
                      cache_id='items_task_id',
                      logger=logger)
def publish_all_items(debug = False):
    """Write all exported plain text, HTML, SRT and other exported
    transcripts for all items to disk as static files.
    """
    items = Item.objects.filter(track_count__gt=0).select_related()
    total = items.count()
    if debug: items = items[0:10]
    for index, item in enumerate(items):
        publish_all_items.update_progress(float(index) / total, item.name)
        publish_item(item)


def publish_item(item):
    """Write out all exported transcripts for 'item' as static files."""
    for export in item_exports(item):
        if export.visibility in PUBLISH_STATES:
            spindle.utils.mkdir_p(os.path.dirname(export.path))

            with open(export.path, 'wb') as outfile:
                export.write(outfile)
                logger.info(u'\twrote "%s"', export.path)


#
# RSS feed of keywords and plain text
#

class SpindleFeed(Rss201rev2Feed):
    def root_attributes(self):
        attrs = super(SpindleFeed, self).root_attributes()
        for ns, uri in RSS_NAMESPACES.iteritems():
            attrs['xmlns:' + ns] = uri
        return attrs

    def add_visibility_tag(self, handler, entry):
        # Add visibility tag. Using OUCS's custom iTunesU categories
        # for now unless/until we come up with something more specific
        visibility = '0' if entry['visibility'] == 'hidden' else '1'
        handler.addQuickElement('category',
                                attrs=dict(scheme=RSS_VISIBILITY_SCHEME,
                                           term=visibility))

class KeywordFeed(SpindleFeed):
    """A simple RSS feed with an entry for both versions (audio and
    video) of each item. Each entry contains keyword (category) tags
    and a link to the item's plain text transcript.
    """
    def add_item_elements(self, handler, entry):
        super(KeywordFeed, self).add_item_elements(handler, entry)

        self.add_visibility_tag(handler, entry)

        for keyword in entry['keywords']:
            handler.addQuickElement('category', attrs={'term': keyword})

        for ngram in entry['ngrams']:
            handler.addQuickElement('category', attrs={'term': ngram})

@single_instance_task(name='spindle.publish.keywords_feed',
                      cache_id='keyword_field_task_id',
                      logger=logger)
def publish_keywords_feed(debug=False):
    """Publish the RSS feed of plain text transcripts and keywords
    tags for each item.
    """
    feed = KeywordFeed(title = "Spindle keywords", link = "/",
                       description = "Text transcripts and keywords generated by Spindle")
    items = Item.objects.filter(track_count__gt=0).order_by('-updated')
    if debug: items = items[0:10]

    publish_keywords_feed.update_progress(0, u"URL = {}\nPath = {}".format(
        KEYWORDS_RSS_URL, KEYWORDS_RSS_FILENAME))
    total = len(items)
    for index, item in enumerate(items):
        publish_keywords_feed.update_progress(float(index) / total, item.name)

        # Consider only plain text exports
        for export in filter(lambda export: export.mime_type == 'text/plain',
                             item_exports(item)):

            # Compute keywords
            keywords, ngrams = track_keywords(export.track)
            keywords = map(lambda kw_ll: kw_ll[0],
                           filter(lambda kw_ll: kw_ll[1] > LL_THRESHOLD, keywords))
            ngrams = map(lambda ng: u' '.join(ng[0]), ngrams)

            logger.info('\t%d keywords, %d ngrams', len(keywords), len(ngrams))
            logger.debug('%s', '\tKeywords:' + u', '.join(keywords))
            logger.debug('%s', '\tNgrams:' + u', '.join(ngrams))

            # Add an entry for both the audio and video versions. This
            # is so our Drupal system, which treats the audio and
            # video as separate nodes, can import transcript
            # information automatically for both.
            for guid in filter(None, (item.audio_guid, item.video_guid)):
                feed.add_item(title=item.name, unique_id=guid,
                              link=export.href,
                              description=export.description,
                              visibility=export.visibility,
                              keywords=keywords, ngrams=ngrams)

    with open(KEYWORDS_RSS_FILENAME, 'wb') as outfile:
        feed.write(outfile, 'utf-8')


#
# RSS feed of all exported transcripts.
#

class TranscriptFeed(SpindleFeed):
    """RSS feed with one entry for each exported form of each transcript."""
    def add_item_elements(self, handler, entry):
        super(TranscriptFeed, self).add_item_elements(handler, entry)

        self.add_visibility_tag(handler, entry)

        # Add links referencing the GUID of the imported item record
        item = entry['model_obj']
        for guid in filter(None, (item.audio_guid, item.video_guid)):
            handler.addQuickElement('atom:link',
                                    attrs={ 'rel': 'related',
                                            'href': guid }) 

@single_instance_task(name='spindle.publish.exports_feed',
                      cache_id='export_feed_task_id',
                      logger=logger)
def publish_exports_feed(debug=False):
    feed = TranscriptFeed(title = "Spindle transcripts",
                          link = "/",
                          description = "Text, SRT, and HTML transcripts generated by Spindle")
    items = Item.objects.filter(track_count__gt=0).order_by('-updated')
    if debug: items = items[0:10]

    logger.info(u"URL = {}\nPath = {}".format(EXPORTS_RSS_URL, EXPORTS_RSS_FILENAME))
    total = len(items)
    for index, item in enumerate(items):
        publish_exports_feed.update_progress(float(index) / total, item.name)
        for export in item_exports(item):
            feed.add_item(title=item.name,
                          link=export.href,
                          description=export.description,

                          visibility=export.visibility,
                          model_obj=item)

    with open(EXPORTS_RSS_FILENAME, 'wb') as outfile:
        feed.write(outfile, 'utf-8')



#
# Utilities to extract export information from each item
#

def item_exports(item):
    """Generator, returning attributes for all the exported URLs
    associated with 'item'.
    """
    base_name = item_basename(item)
    if not base_name: return

    for track in item.track_set.filter(clip_count__gt=0):
        base_path = os.path.join(track_directory(track), base_name)
        base_url = urlparse.urljoin(track_url(track), base_name)
        for export_type in EXPORT_TYPES:
            visibility = getattr(track, export_type.visibility_field)
            if visibility in PUBLISH_STATES:
                yield Export(href = base_url + export_type.extension,
                             path = base_path + export_type.extension,
                             lang = track.lang,
                             rel = export_type.rel,
                             mime_type = export_type.mime_type,
                             description = export_type.description,
                             visibility = visibility,
                             write = getattr(track, export_type.write_method),
                             track = track)


def track_keywords(track):
    """Compute keywords and n-grams for a track."""
    text = (clip.caption_text
            for clip in track.clip_set.all())
    return keywords_and_ngrams(text)

def item_basename(item):
    """Return a base filename to use for 'item', based on its audio or
    video url.

    >>> 'http://some.server/dir/path/file.mp3' => 'file'"""
    url = item.audio_url or item.video_url
    if not url: return None
    return os.path.splitext(os.path.basename(urlparse.urlparse(url).path))[0]


def track_directory(track):
    """Return an absolute path to the directory where published files
    for 'track' will be written."""
    return os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY, str(track.id))


def track_url(track):
    """Return the public URL of the directory containing published
    files for 'track'."""
    return urlparse.urljoin(PUBLIC_URL, str(track.id)) + '/'
