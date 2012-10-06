
import tempfile
import requests
from requests.auth import HTTPBasicAuth
import os
import sys
import logging
import time
import xml.etree.ElementTree as ET

from django.conf import settings


# Utility: make Koemei API requests
KOEMEI_API_BASE = 'http://www.koemei.com/REST/'
def koemei_api_request(method, route, data=None, files=None):
    auth = HTTPBasicAuth(settings.SPINDLE_KOEMEI_USERNAME,
                         settings.SPINDLE_KOEMEI_PASSWORD)
    headers = { 'accept': 'text/xml' }
    config = { 'verbose': sys.stderr }

    if method == 'GET':
        req = requests.get(KOEMEI_API_BASE + route,
                           config=config, auth=auth, headers=headers)
    elif method == 'POST':
        req = requests.post(KOEMEI_API_BASE + route,
                            config=config, auth=auth, headers=headers,
                            files=files, data=data, allow_redirects=True)
    else:
        raise Exception(u'Unknown or unimplemented HTTP method {}'.format(method))

    req.raise_for_status()
    return ET.fromstring(req.content)

# Step 1: Upload media to Koemei, return UUID
def upload(url, logger=logging.getLogger(__name__)): 
    logger.info(u"Downloading '{}' ...".format(url))
    current_task.update_state(
        state='DOWNLOADING',
        meta={'url': url})
    request = requests.get(url)
    request.raise_for_status()
    logger.info("... downloaded ok")

    infile = tempfile.NamedTemporaryFile()
    logger.info("Saving '{}' to '{}'...".format(url, infile.name))
    infile.write(request.content)
    logger.info("... saved ok")
 
    infile.seek(0,0)
    logger.info("Uploading '{}' to Koemei".format(infile.name))
    data = koemei_api_request('POST', 'media', files={ 'media': infile })
    logger.info("... uploading ok")
    return data.find('.//id').text

# Step 1 (alternative): Upload directly from URL
def upload_direct(url, logger=logging.getLogger(__name__)):
    logger.info(u"Uploading URL '{}' to Koemei".format(url))
    data = koemei_api_request('POST', 'media', data={ 'media': url })
    logger.info("... uploading ok")
    return data.find('.//id').text


# Step 2: Given UID, request transcription, and return URL route to
# transcription process
def request_transcription(uuid, logger=logging.getLogger(__name__)):
    logger.info(u"Requesting transcription for '{}' ...".format(uuid))
    data = koemei_api_request('POST', 
                              'media/{}/transcribe'.format(uuid))
    logger.info("... request made")
    href = data.find('.//{http://www.w3.org/2005/Atom}link').attrib['href']
    return href.split(KOEMEI_API_BASE)[1]

# Return status of transcription
# Return value is a tuple: (status, progress, transcript)
def transcription_status(route, logger=logging.getLogger(__name__)):
    data = koemei_api_request('GET', route)

    if(data.tag == 'segmentation'):
        return 'FINISHED', 1, data
    else:    
        # states: PENDING, RUNNING
        status = data.find('.//state').text
        progress = float(data.find('.//progress').text)/100
        return status, progress, None

#@task()
# def transcribe(item):
#     url = item.audio_url if item.audio_url else item.video_url

#     uuid = upload_direct(url)
#     route = request_transcription(uuid)

#     while True:
#         status, progress, data = transcription_status(route)
#         print "{}: {}".format(status, progress)
#         if data is not None:
#             break
#         time.sleep(60)

