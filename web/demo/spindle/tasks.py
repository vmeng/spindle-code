from pprint import pprint, pformat

from django.conf import settings

from celery import task, current_task
from celery.utils.log import get_task_logger

import spindle.readers.feedscraper
import spindle.models
from spindle.templatetags.spindle_extras import duration as format_duration

logger = get_task_logger(__name__)

# Scrape the RSS feed
@task(queue="local")
def scrape():
    # Make a hash of all URLs in database
    urlhash = {}
    print "Listing all URLs in database ..."
    for item in spindle.models.Item.objects.all():
        urlhash[item.audio_url] = urlhash[item.video_url] = item
    print " ... got {} URLs".format(len(urlhash))

    # Scrape RSS for items
    try:
        url = settings.SPINDLE_SCRAPE_RSS_URL
        if not url: raise AttributeError
    except AttributeError:
        raise Exception("SPINDLE_SCRAPE_RSS_URL is blank or unset in settings.py")

    print u"Scraping RSS feed at '{}' ...".format(url)
    rss = spindle.readers.feedscraper.extract(url)

    def update_kw(item, entry):
        if item.keywords != entry['keywords']:
            print u'Updating item keywords for \'{}\':\n{}\n'.format(
                item.name, entry['keywords'])
            item.keywords = entry['keywords']
            return True
        return False

    # Check for items to be added or updated
    newitems = []

    for entry in rss:
        rss_urls = [f for f in ['audio_url', 'video_url'] if f in entry]
        existing_urls = dict((f, entry[f])
                             for f in rss_urls if entry[f] in urlhash)

        if len(rss_urls) and not existing_urls:
            # This item doesn't exist at all yet
            item = spindle.models.Item(**entry)
            print u"New item: '{}'".format(item.name)
            newitems.append(item)
            item.save()
        elif len(existing_urls) == len(rss_urls):
            # Already have both URLs in db, but should check keywords
            item = urlhash[existing_urls.items()[0][1]]
            if update_kw(item, entry): item.save()
        elif len(existing_urls) < len(rss_urls):
            # We have one URL but not the other: update
            existing_field, existing_url = existing_urls.items()[0]
            item = urlhash[existing_url]
            new_field = 'video_url' if existing_field == 'audio_url' else 'audio_url'
            print u'Updating item \'{}\' to include {}=\'{}\''.format(
                item.name, new_field, entry[new_field])
            setattr(item, new_field, entry[new_field])

            # Also check for keyword update
            update_kw(item, entry)

            item.save()

    print 'added {} new items to database'.format(len(newitems))
    return newitems

@task()
def ping():
    request = current_task.request
    status = 'Executing task id {} on {}'.format(request.id, request.hostname);
    print status
    return status
