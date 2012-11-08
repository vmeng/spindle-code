import time

from django.conf import settings

from celery import task, current_task
from celery.utils.log import get_task_logger

from . import sphinx
import spindle.models
from spindle.templatetags.spindle_extras import duration as format_duration
from spindle.transcribe.save import save_transcription

logger = get_task_logger(__name__)

#
# Transcribe an item using Sphinx
#
@task(name="spindle_transcribe_sphinx", queue="sphinx")
def transcribe(item):
    url = item.audio_url if item.audio_url else item.video_url

    infile, wavfile = sphinx.transcode(url,
                                       current_task=current_task,
                                       log=logger.info)

    current_task.update_state(
        state='PROGRESS',
        meta={'time': 0, 'duration': item.duration, 'progress': 0, 'eta': None}
        )

    clips = []
    lastProgress, lastTime = 0, time.time()

    for clip in sphinx.transcribe_wavfile(wavfile, log=logger.info):
        clips.append(clip)
        progress = clip.outtime / item.duration
        dp = progress - lastProgress
        dt = time.time() - lastTime
        eta = (1 - progress) * (dt / dp)

        logger.info(u"{:.0f}s {:.0f}% eta:{} '{}'".format(
                clip.outtime, progress * 100,
                format_duration(int(eta)),
                clip.caption_text))

        current_task.update_state(
            state='PROGRESS',
            meta={ 'time': clip.outtime, 'duration': item.duration,
                   'progress': progress, 'eta': eta }
            )

    # raw_files=[dict(content_type='text/plain',
    #                 file_name='sphinx.output.text',
    #                 body='')]

    save_transcription(item, clips=clips, engine=current_task.name,
                       logger = logger)
