"""Save the transcript produced by a transcription engine (Sphinx,
Koemei).

This was originally a separate task run in a pipeline after the
transcription task, but that turns out to be too fragile and
unpredictable.
"""

import logging
from django.db import transaction
from spindle.models import Item, Track, Clip, Speaker

def save_transcription(item, clips, speakers=None, engine=None, raw_files=None,
                       logger=None):
    """
    Save an automatically-generated transcript for `item`.

    `clips`: Array of Clip objects

    `speakers`: (optional): Array of Speaker objects

    `engine`: FIXME

    `raw_files`: FIXME Any raw files resulting from the transcription.
    Each file is represented by a dict with keys `content_type`,
    `file_name` and `body`.
    """
    if not speakers: speakers = []
    if not logger: logger = logging.get_logger(__name__)

    logger.info(u"Saving transcript with %d speakers, %d clips for item %s",
                len(speakers), len(clips), item)

    with transaction.commit_on_success():
        track = Track(item=item, kind='captions', name='Automatic transcription')
        track.save()

        for speaker in speakers:
            speaker.track = track
            speaker.save()

        for clip in clips:
            # Despite appearances, the following line is actually
            # necessary to make the speaker_id foreign key update
            # correctly. Yuck.
            clip.speaker = clip.speaker # Necessary!
            clip.track = track

        Clip.objects.bulk_create(clips)
