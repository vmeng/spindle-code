from pprint import pprint, pformat

from django.conf import settings

import os.path
import itertools

from celery import task, current_task
from celery.utils.log import get_task_logger

import xml.etree.ElementTree as ET
from spindle.transcribe.koemei import reader

logger = get_task_logger(__name__)

# Read saved Koemei test data for an item
@task(name="spindle_test_koemei", queue="koemei_test")
def transcribe(item):
    data_dir = settings.SPINDLE_KOEMEI_TEST_DATA_DIR
    file_name = os.path.join(data_dir, str(item.id) + ".xml")
    logger.info("Trying to read {}".format(file_name))

    try:
        infile = open(file_name)
    except:
        raise Exception("Unable to open {}".format(file_name))

    data = ET.parse(infile) 
    transcript = reader.read(data)
    transcript['task_name'] = current_task.name

    return transcript
