import os
import xml.etree.ElementTree as ET
import requests
import urlparse

from django.conf import settings
from django.db.models import Q

from spindle.models import Item, PUBLISH_STATES
import spindle.keywords.collocations as collocations
import spindle.utils
    
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

# construct a qualified name for <atom:link>
ATOM_LINK_QNAME = ET.QName(RSS_NAMESPACES['atom'], 'link')
                           
def publish_feed():
    """Republish the incoming RSS feed, adding keywords and links.""" 
    in_url = settings.SPINDLE_SCRAPE_RSS_URL

    items = spindle.models.Item.objects.bulk_fetch(select_related=True)

    print 'Getting original RSS feed to annotate...'
    resp = requests.get(in_url, prefetch=False)
    print 'Parsing RSS...'
    rss = ET.fromstringlist(resp.iter_lines())

    def add_category_tag(entry, scheme, term):
        tag = ET.SubElement(entry, 'category')
        tag.attrib['scheme'] = scheme
        tag.attrib['term'] = term

    entries = rss.findall('.//entry')
    total = len(entries)
    for index, entry in enumerate(entries):
        href = entry.find('link').attrib['href']
        title = entry.find('title').text
        print u'{:5.1f}% {:5d} {}'.format(100 * float(index) / total, index, title)

        if href in items.audio:
            item = items.audio[href]
        elif href in items.video:
            item = items.video[href]
        else:
            print u'\t[no item found]'
            continue
                
        if item.clip_count:
            print "Keywords: "
            keywords, ngrams = item_keywords(item)
            for keyword, ll in keywords:
                add_category_tag(entry, RSS_KEYWORDS_SCHEME, keyword)
                print '\t', keyword                
            for ngram, count in ngrams:
                ngram_string = ' '.join(ngram)
                add_category_tag(entry, RSS_NGRAMS_SCHEME, ngram_string)
                print '\t', ngram_string
            print '\n'

        for attributes in published_urls(item):
            tag = ET.SubElement(entry, ATOM_LINK_QNAME, attributes)
            print '\t{} {} {}'.format(attributes['rel'].split('/')[-1],
                                      attributes['hreflang'],
                                      attributes['href'])
    
    print 'Writing RSS...'
    for prefix, uri in RSS_NAMESPACES.iteritems():
        ET.register_namespace(prefix, uri)

    tree = ET.ElementTree(rss)
    outfile = open(os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY,
                                settings.SPINDLE_PUBLISH_RSS_FILENAME),
                   'wb')

    tree.write(outfile, encoding='utf-8', xml_declaration=True)
    print 'Done'


def item_keywords(item):
    text = (clip.caption_text
            for track in item.track_set.all()
            for clip in track.clip_set.all())
    kw, ngrams = collocations.keywords_and_ngrams(text) 
    return (kw, ngrams)

def item_basename(item):
    url = item.audio_url or item.video_url
    if not url: return None
    return os.path.splitext(os.path.basename(urlparse.urlparse(url).path))[0]

def track_directory(track):
    return os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY, str(track.id))

def track_url(track):    
    return urlparse.urljoin(settings.SPINDLE_PUBLIC_URL, str(track.id)) + '/'

def publish_item(item):
    base_name = item_basename(item)
    if not base_name: return

    for track in item.track_set.filter(clip_count__gt=0):
        dir_name = track_directory(track)
        spindle.utils.mkdir_p(dir_name)
        base_path = os.path.join(dir_name, base_name)
        if track.publish_text in PUBLISH_STATES:
            with open(base_path + '.txt', 'wb') as outfile:
                print '\t{}'.format(outfile.name)
                track.write_plaintext(outfile)

        if track.publish_vtt in PUBLISH_STATES:
            with open(base_path + '.vtt', 'wb') as outfile:
                print '\t{}'.format(outfile.name)
                track.write_vtt(outfile)

        if track.publish_transcript in PUBLISH_STATES:
            with open(base_path + '.html', 'wb') as outfile:
                print '\t{}'.format(outfile.name)
                track.write_html(outfile)

def published_urls(item):
    base_name = item_basename(item)
    if not base_name: return

    for track in item.track_set.filter(clip_count__gt=0):
        base_path = os.path.join(track_directory(track), base_name)
        base_url = urlparse.urljoin(track_url(track), base_name)
        for field, extension, name, ctype, rel in (
            ('publish_text', '.txt', 'Plain text transcript',
             'text/plain', RSS_TRANSCRIPT_REL),
            ('publish_vtt', '.vtt', 'WebVTT captions',
             'text/vtt', RSS_CAPTIONS_REL),
            ('publish_transcript', '.html', 'HTML transcript',
             'text/html', RSS_TRANSCRIPT_REL)):
            publish = getattr(track, field)
            if publish in PUBLISH_STATES:
                if publish == 'hidden':
                    rel += 'hidden/'
                yield dict(href = base_url + extension,
                           hreflang = track.lang,
                           rel = rel,
                           type = ctype)

def publish_all_items():
    items = Item.objects.filter(clip_count__gt=0).select_related()
    total = items.count()
    for index, item in enumerate(items):
        print u'{:5.1f}% {:5d} {}'.format(100 * float(index) / total, index, item.name )
        publish_item(item)
