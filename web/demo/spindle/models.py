import os
import datetime
import operator
import StringIO
import tempfile
import subprocess
import sys

from django.db import models, transaction
from django.db.models import Q, Count, Sum
from django.core import serializers
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils import timezone

from celery.result import BaseAsyncResult

import xml.etree.ElementTree as ET
from pprint import pprint

from spindle.utils import mkdir_p
import spindle.transcribe

#
# An item represents a single podcast for transcription. It has a
# title, duration, published date, possibly both audio and video
# URLs, and any number of transcription 'tracks'.
#

class ItemHash():
    audio = {}
    video = {}

# The Item manager class
class ItemManager(models.Manager):
    def get_query_set(self):
        return super(ItemManager, self).get_query_set() \
            .annotate(track_count=Count('track'))

    def bulk_fetch(self, select_related=False):
        """Return hashes of all items in the database indexed by URL.

        The return value is an object with 'audio' and 'video'
        attributes. Each is a hash from the appropriate type of URLs
        to Item objects.
        """
        ret = ItemHash()
        if select_related:
            query = self.select_related().all()
        else:
            query = self.all()

        for item in query:
            if item.video_url:
                ret.video[item.video_url] = item
            if item.audio_url:
                ret.audio[item.audio_url] = item
        return ret


# The Item instance class
class Item(models.Model):
    objects             = ItemManager()

    name                = models.CharField('Title', max_length=1000)
    video_url           = models.URLField('Video URL', max_length=1000, blank=True)
    audio_url           = models.URLField('Audio URL', max_length=1000, blank=True)
    duration            = models.IntegerField('Length in seconds')
    published           = models.DateTimeField('Date published')

    # RSS keywords/categories, in CSV form
    keywords            = models.TextField(blank=True)

    # Other RSS information
    video_guid          = models.CharField(max_length=500, blank=True)
    audio_guid          = models.CharField(max_length=500, blank=True)
    licence_long_string = models.CharField(max_length=200, blank=True)

    # Version tracking
    updated             = models.DateTimeField('Last updated',
                                               auto_now=True,
                                               auto_now_add=True,
                                               editable=False)
    updated_by          = models.ForeignKey(User, null=True, blank=True,
                                            editable=False)

    def __unicode__(self):
        return self.name

    # Return the fraction of this item's transcript that has been
    # edited, or None if there are no existing clips at all.
    def edited_fraction(self):
        tracks = self.track_set.all()
        clip_count = sum(track.clip_count for track in tracks)
        edited_clip_count = sum(track.edited_clip_count for track in tracks)

        if not clip_count: return None
        return float(edited_clip_count) / clip_count

    # Push this item onto the transcription queue
    def request_transcription(self, engine_name='spindle.transcribe.sphinx'):
        transcribe = spindle.transcribe.engine_map[engine_name]['task']

        task = transcribe.delay(self)
        task_record = TranscriptionTask(item = self, task_id = task.id,
                                        engine = engine_name)
        task_record.save()

    # Versioning stuff
    def archive(self, msg=None, commit=True):
        archive = ArchivedItem(item=self)
        archive.save()

    def serialize(self, method):
        return serializers.serialize(method, self.serializable_objects())

    def serializable_objects(self):
        for track in self.track_set.select_related('speaker', 'clip'):
            for speaker in track.speaker_set.all(): yield speaker
            for clip in track.clip_set.all(): yield clip
            yield track
        yield self

    def save(self, *args, **kwargs):
        super(Item, self).save(*args, **kwargs)
        self.archive()

#
# Archived versions of items
#
class ArchivedItem(models.Model):
    item = models.ForeignKey(Item, related_name='versions')
    updated             = models.DateTimeField('Last updated',
                                               auto_now=True,
                                               auto_now_add=True,
                                               editable=False)
    updated_by          = models.ForeignKey(User, null=True, blank=True,
                                            editable=False)
    json = models.TextField('')

    class Meta:
        ordering = ['-updated']

    def __unicode__(self):
        return u'Archive of {}'.format(self.item)

    def save(self, *args, **kwargs):
        self.json = self.item.serialize('json')
        super(ArchivedItem, self).save(*args, **kwargs)

    def deserialized(self):
        return serializers.deserialize('json', self.json)

    def write_diffable_text(self, outfile):
        # Ensure we can iterate several times over serialized if it's
        # a generator
        objs = [obj for obj in self.deserialized()]

        def extract(model):
            return [o.object for o in objs
                    if isinstance(o.object, model)]

        item = extract(Item)[0]
        tracks = sorted(extract(Track),
                        key=operator.attrgetter('id'))
        all_speakers = extract(Speaker)
        all_clips = extract(Clip)

        def write_fields(obj, include=None, exclude=None):
            fields = include if include else [f.name for f in obj._meta.fields]
            if exclude: fields = set(fields).difference(exclude)

            for field in fields:
                outfile.write(u'{}: {}\n'.format(
                        field, getattr(obj, field)))

        write_fields(item)

        for track in tracks:
            speakers = filter(lambda s: s.track_id == track.id,
                              all_speakers)
            clips = sorted(filter(lambda c: c.track_id == track.id,
                                  all_clips),
                           key=operator.attrgetter('intime'))

            outfile.write(u'\n\n\nTrack: {}\n'.format(track.name))
            write_fields(track, exclude=['item', 'name'])

            outfile.write('Speakers:\n')
            for speaker in speakers:
                outfile.write(u'{} {}\n'.format(
                        speaker.id, speaker.name))
            outfile.write('\n\n')

            for clip in clips:
                outfile.write(u'{:8.2f} {:8.2f} {:6}  {}\n'.format(
                        clip.intime, clip.outtime,
                        speaker.id if clip.speaker else '',
                        clip.caption_text))
        outfile.flush()

    def diffable_text(self):
        """Return diffable text as a string"""
        outfile = StringIO.StringIO('')
        self.write_diffable_text(outfile)
        return outfile.getvalue()


    def diff(self, old_version=None):
        """Diff this revision of an item with another revision.
        If `old_version' is None, diffs with the previous revision."""

        if old_version is None:
            # Find previous version and diff with it
            previous_versions = self.item.versions.filter(
                updated__lt = self.updated).order_by(
                '-updated')

            if previous_versions:
                old_version = previous_versions[0]

        tmpfile_1 = tempfile.NamedTemporaryFile()
        self.write_diffable_text(tmpfile_1)

        if old_version is None:       # No previous version: diff with /dev/null
            tmpfile_2 = open("/dev/null")
        else:
            tmpfile_2 = tempfile.NamedTemporaryFile()
            old_version.write_diffable_text(tmpfile_2)

        diff_file = tempfile.NamedTemporaryFile()
        errcode = subprocess.call([
                'diff', '-u',
                tmpfile_2.name,
                tmpfile_1.name],
                                  stdout=diff_file,
                                  stderr=sys.stderr)

        diff_file.seek(0, 0)
        for line in diff_file: yield line

    def revert(self):
        self.item.track_set.all().delete()

        objects = self.deserialized()
        for obj in objects:
            obj.save()

        return None


# Transcription tasks associated to an item
class TranscriptionTask(models.Model):
    queue       = models.Manager()
    item        = models.ForeignKey(Item)
    task_id     = models.CharField(max_length=100, blank=True)
    engine      = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "{} {} {}".format(
            self.item.name,
            self.engine,
            self.task_id)

    # Return the Celery task object, if any
    def async_result(self):
        if self.task_id:
            return BaseAsyncResult(self.task_id)
        else:
            return None

    def status(self):
        return self.async_result().status

    def result(self):
        return self.async_result().result


# Aggregate function to sum booleans with type cast in PostgreSQL
class SumAsIntSQL(models.sql.aggregates.Aggregate):
    sql_function = 'SUM'
    sql_template = 'SUM( %(field)s :: int)'

class SumAsInt(models.Aggregate):
    name = 'SumInt'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = SumAsIntSQL(col,
                                source=source,
                                is_summary=is_summary,
                                **self.extra)
        query.aggregates[alias] = aggregate


# A track is a collection of clips, and possibly of speaker names.
from django.conf.global_settings import LANGUAGES
TRACK_KINDS = (('captions', 'Captions'),   # What's the difference
               ('subtitles', 'Subtitles'), # between these two?
               ('chapters', 'Chapters'),
               ('notes', 'Notes'),
               ('metadata', 'Metadata'))

PUBLISHED_STATES = (('no', 'No'),
                    ('hidden', 'Hidden'),
                    ('public', 'Public'))
PUBLISH_STATES = ('hidden', 'public')


class TrackManager(models.Manager):
    # Count # of clips and edited clips
    def get_query_set(self):
        return super(TrackManager, self).get_query_set() \
            .annotate(clip_count=Count('clip')) \
            .annotate(edited_clip_count=SumAsInt('clip__edited'))

class Track(models.Model):
    objects = TrackManager()

    item = models.ForeignKey(Item)
    name = models.CharField(max_length=1000,
                            blank=True,
                            default='Transcript')
    kind = models.CharField(max_length=10,
                            choices=TRACK_KINDS,
                            default='captions')
    lang = models.CharField('Language', max_length=7,
                            choices=LANGUAGES,
                            default='en')

    publish_text = models.CharField('Publish plaintext',
                                    max_length=6,
                                    choices=PUBLISHED_STATES,
                                    default='hidden')
    publish_vtt = models.CharField('Publish captions',
                                   max_length=6,
                                   choices=PUBLISHED_STATES,
                                   default='no')
    publish_transcript = models.CharField('Publish transcript',
                                          max_length=6,
                                          choices=PUBLISHED_STATES,
                                          default='no')

    def __unicode__(self):
        return u'{} ({}, {})'.format(
            self.item.name, self.kind, self.lang)

    def save(self):
        super(Track, self).save()
        self.item.archive()

    # Make an empty transcript for this item
    @classmethod
    def empty(cls, item, cliplength=4.0, **kwargs):
        if not item.duration:
            raise Error(u"Unknown or zero item duration for item {}".format(item))

        track = Track(item=item, **kwargs)
        intime = 0.0
        while intime < item.duration:
            clip = Clip(track=track,
                        intime=intime,
                        outtime=intime + cliplength,
                        caption_text="",
                        edited=False)
            clip.save()
            intime += cliplength

        track.save()
        return track

    # Fraction of this transcript that has been edited, or None if
    # there are no existing clips at all.
    def edited_fraction(self):
        if not self.clip_count: return None
        return float(self.edited_clip_count) / self.clip_count


    # Export as plain text
    def write_plaintext(self, outfile):
        speaker_id = None
        for clip in self.clip_set.all():
            if clip.begin_para:
                outfile.write('\n\n');
            if clip.speaker and clip.speaker.id != speaker_id:
                outfile.write(clip.speaker.name.upper() + ": ")
                speaker_id = clip.speaker.id
            outfile.write(clip.caption_text.strip() + " ")

    # Export as HTML
    def write_html(self, outfile):
        from django.template.loader import get_template
        transcript = ET.Element('div')
        speaker_id = None

        for idx, clip in enumerate(self.clip_set.all()):
            # Begin new paragraph if indicated
            if idx == 0 or clip.begin_para:
                para = ET.SubElement(transcript, 'p')
                para.text = ''
                speaker_elem = None

            # Speaker change?
            if clip.speaker and clip.speaker.id != speaker_id:
                speaker_id = clip.speaker.id
                speaker_elem = ET.SubElement(para, 'span',
                                             { 'class': 'speaker' })
                speaker_elem.text = clip.speaker.name.strip() + ": "
                speaker_elem.tail = ''

            # Yuck.
            if speaker_elem is not None:
                speaker_elem.tail += clip.caption_text.strip() + " "
            else:
                para.text += clip.caption_text.strip() + " "

        outfile.write(render_to_string('spindle/export-transcript.html', {
                'item': self.item,
                'transcript': ET.tostring(transcript),
                'date': timezone.now()
                }))

    # Export as VTT
    def write_vtt(self, outfile):
        import spindle.writers.vtt
        spindle.writers.vtt.write(self.clip_set.all(), outfile)

#
# Each track may have several speakers.
#
class Speaker(models.Model):
    track = models.ForeignKey(Track)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name

#
# A transcription track is made up of many clips. Each clip is a small
# amount of text ('caption_text'), (possibly) spoken by a given
# 'speaker', lasting for a span of time from 'intime' to 'outtime'. A
# clip may also be marked as beginning a new paragraph in the
# transcript.
#
class Clip(models.Model):
    track        = models.ForeignKey(Track)
    intime       = models.FloatField()
    outtime      = models.FloatField()
    caption_text = models.TextField()
    edited       = models.BooleanField()
    speaker      = models.ForeignKey(Speaker, null=True, blank=True)
    begin_para   = models.BooleanField()

    class Meta:
        ordering = ['intime']

    def __unicode__(self):
        return self.caption_text
