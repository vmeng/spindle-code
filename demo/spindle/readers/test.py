from feedscraper import rss_to_records, records_to_items
rss = ''

import itertools

rec = rss_to_records(rss)
items = records_to_items(rec)

from pprint import pprint 
for i in items:
    if 'audio_url' in item and 'video_url' in item:
        pprint(i)
