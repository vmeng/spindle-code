"""Module for exporting various formats of Spindle transcripts and an
RSS feed as static files.

"""

import os
import os.path
import urlparse
import logging
import time

from django.conf import settings
from django.utils.feedgenerator import Rss201rev2Feed, Enclosure
from django.utils.timezone import now

from spindle.models import Item, PUBLISH_STATES
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

# Filename for published RSS feed
EXPORTS_RSS_FILENAME = os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY,
                                    settings.SPINDLE_EXPORTS_RSS_FILENAME)

# URL for published RSS feed
EXPORTS_RSS_URL = urlparse.urljoin(PUBLIC_URL,
                                   settings.SPINDLE_EXPORTS_RSS_FILENAME)
    
class Export:
    """An exported transcript for a particular track in a particular format.

    Subclasses of Export create plain text, HTML and VTT exported
    files.

    For each track, all the exported files are written to the
    directory SPINDLE_PUBLIC_DIRECTORY/TRACK_ID.  Each export creates
    two files: one with a filename including a date and time stamp,
    and a symbolic link to the timestamped file whose filename/URL
    does not change.  Having a filename which changes each time the
    track is exported makes it easier to propagate changes to
    consumers of the RSS feed when the content of a transcript
    changes.

    """

    # Name of the Track model field controlling whether this type of
    # file should be exported
    visibility_field = None
    
    # Name of the Track model method that writes this type of file
    write_method = None
    
    extension = None
    description = None
    mime_type = None
    
    # String to use in the <link> tag in exported RSS:
    rel = None

    def __init__(self, track):
        self.track = track

    def write(self):
        """Write an exported transcript to disk.  Creates a newly timestamped file
        """
        write_method = getattr(self.track, self.write_method)
        if not os.path.isdir(self.dirname):
            spindle.utils.mkdir_p(self.dirname)
        self.make_new_filename()
        with open(self.filepath, 'wb') as outfile:
            write_method(outfile)
        if os.path.exists(self.linkpath): os.remove(self.linkpath)
        os.symlink(self.filepath, self.linkpath)

    @property
    def file_exists(self):
        """True if exported files already exist for this format.  

        Does not check whether the existing files are out of date with
        respect to the content in the Spindle database.
        """
        return os.path.exists(self.linkpath)

    @property
    def as_enclosure(self):
        """A Django enclosure object for including this exported format in the RSS feed."""
        try:
            return Enclosure(self.href, str(os.path.getsize(self.linkpath)), self.mime_type)
        except:
            return None

    @property
    def href(self):
        """The URL of this exported format.  This URL includes a timestamp,
        and will change when the transcript is edited and re-exported."""
        return urlparse.urljoin(self.url_dirname, self.filename)

    @property
    def guid(self):
        """The permanent URL of this exported format.  This URL points to a
symbolic link, and will not change on editing and re-exporting the
transcript.

        """
        return urlparse.urljoin(self.url_dirname, self.linkname)

    @property
    def filepath(self):
        """Absolute filesystem path to the timestamped file for this exported format."""
        return os.path.abspath(os.path.join(self.dirname, self.filename))

    @property
    def linkpath(self):
        """Absolute filesystem path to the symbolic link for this exported format."""
        return os.path.abspath(os.path.join(self.dirname, self.linkname))

    @property
    def dirname(self):
        """Filesystem path to the directory containing these exported files."""
        return os.path.join(settings.SPINDLE_PUBLIC_DIRECTORY, str(self.track.id))
        
    @property
    def url_dirname(self):
        """URL base for these exported files."""
        return urlparse.urljoin(PUBLIC_URL, str(self.track.id)) + '/'

    @property
    def linkname(self):
        """Filename for the symbolic link. Does not change with each export."""
        return self.basename + self.extension

    _filename = None

    @property
    def filename(self):
        """Timestamped export filename, which changes with each export.

        If a symbolic link already exists for this export, obtain the
        timestamped filename by reading the link.  Otherwise, generate
        a new timestamped filename and return that.
        """
        if self._filename is not None: return self._filename
        try: 
            self._filename = os.path.basename(os.readlink(self.linkpath))
        except:
            self.make_new_filename()
        return self._filename
        
    def make_new_filename(self):
        """Create a new timestamped filename and set self.filename to it."""
        # The following might be technically better, but it leads to
        # longer filenames with funny characters which may cause problems:

        # timestamp = now().isoformat()
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
        self._filename = self.basename + '__' + timestamp + self.extension
        
    @property
    def basename(self):
        """Filename fragment for generating exported filenames.

        Taken from the associated track's audio or video URL, if
        possible.
        """
        url = self.track.item.audio_url or self.track.item.video_url
        if not url: return "transcript"
        return os.path.splitext(os.path.basename(urlparse.urlparse(url).path))[0]

    @property
    def visibility(self):
        """Publishing state of this export format: unpublished, hidden, or public."""
        return getattr(self.track, self.visibility_field) 

    @property
    def is_published(self):
        """True if this exported transcript is either hidden or public."""
        return self.visibility in PUBLISH_STATES

    @property
    def needs_export(self):
        """Whether this transcript format needs exporting.  

        True if this exported file should be published, and exported
        file on disk is either missing or is older than the Track or
        Item model "updated" field.

        """
        if not self.is_published: return False
        if not os.path.exists(self.linkpath): return True
        
        file_updated = os.path.getmtime(self.linkpath)
        track_updated = time.mktime(self.track.updated.timetuple())
        item_updated = time.mktime(self.track.item.updated.timetuple())
        if track_updated > file_updated or item_updated > file_updated:
            return True
        else:
            return False

class TextExport(Export):
    """Plain text transcript export."""
    visibility_field = 'publish_text'
    extension = '.txt'
    description = 'Plain text transcript'
    mime_type = 'text/plain'
    rel = RSS_TRANSCRIPT_REL
    write_method = 'write_plaintext'

class VTTExport(Export):
    """WebVTT/SRT transcript export."""
    visibility_field = 'publish_vtt'
    extension = '.vtt'
    description = 'WebVTT captions'
    mime_type = 'text/vtt'
    rel = RSS_CAPTIONS_REL
    write_method = 'write_vtt'

class HTMLExport(Export):
    """HTML transcript export."""
    visibility_field = 'publish_transcript'
    extension = '.html'
    description = 'HTML transcript'
    mime_type = 'text/html'
    rel = RSS_TRANSCRIPT_REL
    write_method = 'write_html'


# The types of exports
EXPORT_TYPES = (TextExport, VTTExport, HTMLExport)



#
# Procedures for exporting transcripts for all items or for one
# particular item
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
        if export.needs_export:
            export.write()
            logger.info(u'\twrote "%s"', export.filepath)

def item_exports(item):
    """Generator, returning Export instances for each exported format
    associated with 'item'.

    """
    for track in item.track_set.filter(clip_count__gt=0):
        for export_type in EXPORT_TYPES:
            export = export_type(track)
            if export.is_published: yield export

#
# The RSS feed of exported files and extracted keywords
#
class TranscriptFeed(Rss201rev2Feed):
    """RSS feed containing one entry for each exported form of each transcript."""
    def root_attributes(self):
        attrs = super(TranscriptFeed, self).root_attributes()
        for ns, uri in RSS_NAMESPACES.iteritems():
            attrs['xmlns:' + ns] = uri
            return attrs

    def add_item_elements(self, handler, entry):
        super(TranscriptFeed, self).add_item_elements(handler, entry)

        export = entry['spindle_export']
        
        self.add_item_visibility_tag(handler, export)
        self.add_item_original_guid_links(handler, export)
            
        # Add keyword tags on exported plaintext only
        if export.mime_type == 'text/plain':
            self.add_item_category_tags(handler, export)

    def add_item_visibility_tag(self, handler, export):
        """Add visibility tag for this exported file."""
        visibility = '0' if export.visibility == 'hidden' else '1'
        handler.addQuickElement('category',
                                attrs=dict(scheme=RSS_VISIBILITY_SCHEME,
                                           term=visibility))

    def add_item_original_guid_links(self, handler, export):
        """Add tags referencing the GUIDs of the audio and video associated with this exported file.

        These GUIDs are taken from the imported RSS feed, and allow
        cross-referencing between the imported and exported RSS
        files.
        """ 
        item = export.track.item
        for guid in filter(None, (item.audio_guid, item.video_guid)):
            handler.addQuickElement('atom:link',
                                    attrs={ 'rel': 'related',
                                            'href': guid })

    def add_item_category_tags(self, handler, export):
        """Add keyword (category) tags for keywords extracted from this track."""
        for keyword in export.track.keywords:
            handler.addQuickElement('category', attrs={ 'term': keyword })


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
            if export.file_exists:
                # Force computation of keywords inside this loop if
                # necessary.  This allows for more accurate progress
                # updates.
                keywords = export.track.keywords
                feed.add_item(title=item.name,
                              link=export.href,
                              unique_id=export.guid,
                              description=export.description,

                              enclosure=export.as_enclosure,
                              spindle_export=export)

    with open(EXPORTS_RSS_FILENAME, 'wb') as outfile:
        feed.write(outfile, 'utf-8')
