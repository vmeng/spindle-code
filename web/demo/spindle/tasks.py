from pprint import pprint, pformat

from django.conf import settings
from django.core.cache import cache

from celery import task, current_task
from celery.utils.log import get_task_logger

import spindle.readers.feedscraper
import spindle.models
from spindle.templatetags.spindle_extras import duration as format_duration
from spindle.single_instance_task import single_instance_task
from spindle.publish import publish_feed, publish_all_items, publish_exports_feed

logger = get_task_logger(__name__)
SCRAPE_TASK_ID = 'scrape_task_id'


# Scrape the RSS feed
@single_instance_task(cache_id=SCRAPE_TASK_ID, name='spindle_scrape', queue='local')
def scrape():
    current_task.update_progress(.01, 'Listing all URLs in database ...')

    # Make a hash of all URLs in database
    urlhash = {}
    for item in spindle.models.Item.objects.all():
        urlhash[item.audio_url] = urlhash[item.video_url] = item
    current_task.update_progress(.02, " ... got {} URLs".format(len(urlhash)))

    # Scrape RSS for items
    try:
        url = settings.SPINDLE_SCRAPE_RSS_URL
        if not url: raise AttributeError
    except AttributeError:
        raise Exception("SPINDLE_SCRAPE_RSS_URL is blank or unset in settings.py")

    current_task.update_progress(.02, u"Parsing RSS feed at '{}' ...".format(url))
    rss = spindle.readers.feedscraper.extract(url)
    current_task.update_progress(.05, u"Parsing RSS feed at '{}' ... done".format(url))

    def update_kw(item, entry):
        if item.keywords != entry['keywords']:
            logger.info(u'Updating item keywords for \'{}\':\n{}\n'.format(
                item.name, entry['keywords']))
            item.keywords = entry['keywords']
            return True
        return False

    # Check for items to be added or updated
    newitems = []

    num_entries = rss.count
    for index, entry in enumerate(rss.items):
        message = ''
        rss_urls = [f for f in ['audio_url', 'video_url'] if f in entry]
        existing_urls = dict((f, entry[f])
                             for f in rss_urls if entry[f] in urlhash)

        if len(rss_urls) and not existing_urls:
            # This item doesn't exist at all yet
            item = spindle.models.Item(**entry)
            message = u"New item: '{}'".format(item.name)
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
            message = u'Updating item \'{}\' to include {}=\'{}\''.format(
                item.name, new_field, entry[new_field])
            setattr(item, new_field, entry[new_field])

            # Also check for keyword update
            update_kw(item, entry)

            item.save()
        current_task.update_progress(.05 + .94 * (float(index) / num_entries), message)

    current_task.update_progress(1, 'Added {} new items to database'.format(len(newitems)))
    return newitems

@task
def ping():
    request = current_task.request
    status = 'Executing task id {} on {}'.format(request.id, request.hostname);
    logger.info(status)
    return status
