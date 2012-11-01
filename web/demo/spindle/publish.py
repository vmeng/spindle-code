"""Functions relating to publishing transcripts and RSS as static files."""

import os
import xml.etree.ElementTree as ET
import requests
import urlparse
import logging
import sys

from django.conf import settings
from django.db.models import Q

from spindle.models import Item, PUBLISH_STATES
import spindle.keywords.collocations as collocations
import spindle.utils

# Logging
logger = logging.getLogger(__name__)

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
    }

# Namespace for our special-purpose RSS URIs
RSS_SCHEME_ROOT = 'http://rss.oucs.ox.ac.uk/spindle/'

# 'scheme' attributes for RSS <category> tags
RSS_KEYWORDS_SCHEME = RSS_SCHEME_ROOT + 'auto-keywords/'
RSS_NGRAMS_SCHEME = RSS_SCHEME_ROOT + 'auto-ngrams/'

# 'rel' attributes for <atom:link> tags
RSS_TRANSCRIPT_REL = RSS_SCHEME_ROOT + 'transcript/'
RSS_CAPTIONS_REL = RSS_SCHEME_ROOT + 'captions/'

# Pre-computed qualified name for <atom:link> tags
ATOM_LINK_QNAME = ET.QName(RSS_NAMESPACES['atom'], 'link')

# Public URL for published stuff, making sure it ends with a slash
PUBLIC_URL = settings.SPINDLE_PUBLIC_URL
if not PUBLIC_URL.endswith('/'): PUBLIC_URL += '/'


# Descriptions of things to publish. Each entry is a tuple of the form
#
# (flag_field, extension, description, mime_type, rss_rel,
# write_method)
#
# where:
# 'flag_field' is the name of the field in the Track model that
# controls whether this type of file should be exported
#
# 'rss_rel' is the string to use in the <link> tag in exported RSS
#
# 'write_method' is the method on the Track model writing this type of
# file
PUBLISH_TYPES = (('publish_text', '.txt', 'Plain text transcript',
                  'text/plain', RSS_TRANSCRIPT_REL, 'write_plaintext'),
                 ('publish_vtt', '.vtt', 'WebVTT captions',
                  'text/vtt', RSS_CAPTIONS_REL, 'write_vtt'),
                 ('publish_transcript', '.html', 'HTML transcript',
                  'text/html', RSS_TRANSCRIPT_REL, 'write_html'))


def publish_feed(verbose = False, debug = False):
    """Republish the incoming RSS feed, adding <category> tags for
    generated keywords and <link> tags to published transcripts."""
    in_url = settings.SPINDLE_SCRAPE_RSS_URL

    logger.info('Listing items in database...')
    items = spindle.models.Item.objects.bulk_fetch()

    logger.info('Getting original RSS feed to annotate...')
    resp = requests.get(in_url, prefetch=False)
    logger.info('Parsing RSS...')
    rss = ET.fromstringlist(resp.iter_lines())

    def add_category_tag(entry, scheme, term):
        tag = ET.SubElement(entry, 'category')
        tag.attrib['scheme'] = scheme
        tag.attrib['term'] = term

    entries = rss.findall('.//entry')
    total = len(entries)
    if debug: entries = entries[0:10]
    for index, entry in enumerate(entries):
        href = entry.find('link').attrib['href']
        title = entry.find('title').text
        logger.info(u'%5.1f%% %5d %s', 100 * float(index) / total, index, title)

        if href in items.audio:
            item = items.audio[href]
        elif href in items.video:
            item = items.video[href]
        else:
            logger.info(u'\t[no item found]')
            continue

        clip_count = sum(track.clip_count for track in item.track_set.all())
        if clip_count:
            keywords, ngrams = item_keywords(item)

            logger.info('\t%d keywords, %d ngrams', len(keywords), len(ngrams))
            logger.debug('%s', '\tKeywords:' + ', '.join(kw for kw, _ in keywords))
            logger.debug('%s', '\tNgrams:' + ', '.join(' '.join(ng) for ng, _ in ngrams))

            for keyword, ll in keywords:
                add_category_tag(entry, RSS_KEYWORDS_SCHEME, keyword)
            for ngram, count in ngrams:
                ngram_string = ' '.join(ngram)
                add_category_tag(entry, RSS_NGRAMS_SCHEME, ngram_string)

        for attributes in published_urls(item):
            tag = ET.SubElement(entry, ATOM_LINK_QNAME, attributes)
            logger.info(u'\t%s %s %s',
                        attributes['rel'].split('/')[-1],
                        attributes['hreflang'], attributes['href'])

    logger.info('Writing RSS...')
    for prefix, uri in RSS_NAMESPACES.iteritems():
        ET.register_namespace(prefix, uri)

    tree = ET.ElementTree(rss)
    outfile = open(os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY,
                                settings.SPINDLE_PUBLISH_RSS_FILENAME),
                   'wb')

    tree.write(outfile, encoding='utf-8', xml_declaration=True)
    logger.info('Done')


def publish_all_items(verbose = False, debug = False):
    """Write out published contents for all items, as static files."""
    items = Item.objects.filter(track_count__gt=0).select_related()
    total = items.count()
    if debug: items = items[0:10]
    for index, item in enumerate(items):
        logger.info(u'%5.1f%% %5d %s', 100 * float(index) / total, index, item.name)
        publish_item(item)


def publish_item(item):
    """Write out all published contents for 'item' as static files."""
    base_name = item_basename(item)
    if not base_name: return

    for track in item.track_set.filter(clip_count__gt=0):
        dir_name = track_directory(track)
        spindle.utils.mkdir_p(dir_name)
        base_path = os.path.join(dir_name, base_name)
        for field, extension, name, ctype, rel, method in PUBLISH_TYPES:
            visibility = getattr(track, field)
            if visibility in PUBLISH_STATES:
                with open(base_path + extension, 'wb') as outfile:
                    logger.info(u'\twrote %s "%s"', name, outfile.name)
                    (getattr(track, method))(outfile)


def published_urls(item):
    """Generator: yields descriptions of all the published URLs
    associated with 'item'.
    """
    base_name = item_basename(item)
    if not base_name: return

    for track in item.track_set.filter(clip_count__gt=0):
        base_path = os.path.join(track_directory(track), base_name)
        base_url = urlparse.urljoin(track_url(track), base_name)
        for field, extension, name, ctype, rel, method in PUBLISH_TYPES:
            visibility = getattr(track, field)
            if visibility in PUBLISH_STATES:
                if visibility == 'hidden':
                    rel += 'hidden/'
                yield dict(href = base_url + extension,
                           hreflang = track.lang,
                           rel = rel,
                           type = ctype)


def item_keywords(item):
    """Compute keywords and n-grams for an item based on all its
    associated tracks."""
    text = (clip.caption_text
            for track in item.track_set.all()
            for clip in track.clip_set.all())
    kw, ngrams = collocations.keywords_and_ngrams(text)
    return (kw, ngrams)


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
