from django.conf import settings

from celery import task, current_task
from celery.utils.log import get_task_logger

from spindle.transcribe.sphinx import reader

import os.path

logger = get_task_logger(__name__)

# Read Sphinx test data
@task(name="spindle_test_sphinx", queue="sphinx_test")
def transcribe(item):
    data_dir = settings.SPINDLE_SPHINX_TEST_DATA_DIR
    infile = open(os.path.join(data_dir, item.id))

    clips = list(reader.read_clips(infile))

    save_transcription(item, clips=clips, engine=current_task.name,
                       logger = logger)
