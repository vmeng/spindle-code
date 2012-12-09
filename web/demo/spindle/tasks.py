from django.conf import settings

from celery import task, current_task
from celery.utils.log import get_task_logger

import spindle.readers.feedscraper
import spindle.models
from spindle.single_instance_task import single_instance_task
from spindle.publish import publish_keywords_feed, publish_all_items, publish_exports_feed

import logging
logger = logging.getLogger(__name__)

SCRAPE_TASK_ID = 'scrape_task_id'


# Scrape the RSS feed
@single_instance_task(cache_id=SCRAPE_TASK_ID, name='spindle.scrape', queue='local',
                      logger=logger)
def scrape():
    logger.debug("scrape()")
    scrape.update_progress(.01, 'Listing all URLs in database ...')

    # Make a hash of all URLs in database
    urlhash = {}
    for item in spindle.models.Item.objects.all():
        urlhash[item.audio_url] = urlhash[item.video_url] = item
    scrape.update_progress(.02, " ... got {} URLs".format(len(urlhash)))

    # Scrape RSS for items
    try:
        url = settings.SPINDLE_SCRAPE_RSS_URL
        if not url: raise AttributeError
    except AttributeError:
        raise Exception("SPINDLE_SCRAPE_RSS_URL is blank or unset in settings.py")

    scrape.update_progress(.02, u"Parsing RSS feed at '{}' ...".format(url))
    rss = spindle.readers.feedscraper.extract(url)
    scrape.update_progress(.05, u"Parsing RSS feed at '{}' ... done".format(url))

    # Check for items to be added or updated
    newitems = []
    processed_count = 0
    num_entries = rss.count
    for item in rss.items:
        message = ''
        rss_urls = filter(None, (item.audio_url, item.video_url))
        existing_urls = filter(lambda url: url in urlhash, rss_urls)
        if len(rss_urls) and not existing_urls:
            # This item doesn't exist at all yet
            message = u"New item: '{}'".format(item.name)
            newitems.append(item)
            item.save()
        else:
            # Update some fields
            message = u"Updating item '{}':".format(item.name)
            existing_item = urlhash[existing_urls[0]]
            for field in ('audio_guid', 'audio_url',
                          'video_guid', 'video_url',
                          'keywords', 'licence_long_string'):
                value = getattr(item, field)
                if value != getattr(existing_item, field):
                    setattr(existing_item, field, value)
                    message += u"\n\t{}='{}'".format(field, value)
            existing_item.save()
            processed_count += len(rss_urls)
        scrape.update_progress(.05 + .94 * (float(processed_count) / num_entries), message)
        
    scrape.update_progress(1, 'Added {} new items to database'.format(len(newitems)))
    return newitems

@task
def ping():
    request = current_task.request
    status = 'Executing task id {} on {}'.format(request.id, request.hostname);
    logger.info(status)
    return status
