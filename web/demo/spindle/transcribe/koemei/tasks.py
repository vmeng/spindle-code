import time

from celery import task, current_task
from celery.utils.log import get_task_logger

import xml.etree.ElementTree as ET

from spindle.templatetags.spindle_extras import duration as format_duration

from . import reader
from . import koemei_api as koemei

logger = get_task_logger(__name__)

# Transcribe an item using Koemei's service
@task(name="spindle_transcribe_koemei", queue="koemei")
def transcribe(item):
    url = item.audio_url if item.audio_url else item.video_url

    uuid = koemei.upload_direct(url)
    route = koemei.request_transcription(uuid)

    while True:
        status, progress, data = koemei.transcription_status(route)
        logger.info("{}: {}%".format(status, progress * 100))
        if data is not None:
            break

        current_task.update_state(
            state='PROGRESS',
            meta={ 'progress': progress, 'eta': None,
                   'time': None, 'duration': None })
        time.sleep(5 * 60)
        
    transcript = reader.read(data)
    transcript['task_name'] = current_task.name
    transcript['raw_files'] = [dict(content_type='text/xml',
                                    file_name='koemei.transcript.xml',
                                    body=ET.tostring(data))]
    return transcript
