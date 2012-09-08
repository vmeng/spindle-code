"""Module defining word tokens, and how to join them together into clips."""

import spindle.models

class Word():
    """A single word token, with text value, in and out points.

    `intime' and `outtime' are in seconds. `outtime' can be specified directly, or by giving a value for `duration'. 

    `duration' is provided as a computed property of Word objects.
    """
    def __init__(self, token, intime, outtime=None, duration=None):
        self.token = token
        self.intime = intime
        if outtime is None and duration is None:
            raise Error("Must specify `outtime' or `duration' in Word constructor")
        if outtime is not None:
            self.outtime = outtime
        elif duration is not None:
            self.outtime = self.intime + duration

    @property
    def duration(self):
        return self.outtime - self.intime

    def __repr__(self):
        return "<Word: {} ({},{})>".format(
            self.token, self.intime, self.outtime)


def words_to_clips(words, max_time=4, max_words=None, speaker=None):
    """Group words into clips.

    `words' is an iterator over Word objects. Yields `Clip' objects,
    joining words with spaces up to `max_time', the maximum duration
    per clip in seconds.

    TODO: implement `max_words', maximum text length per clip"""

    def start_clip(word):
        return spindle.models.Clip(
            intime = word.intime,
            outtime = word.outtime,
            caption_text = word.token,
            speaker=speaker)

    words = iter(words)
    clip = start_clip(words.next())

    for word in words:
        if word.outtime - clip.intime < max_time:
            clip.caption_text += ' ' + word.token
            clip.outtime = word.outtime
        else:                
            yield clip
            clip = start_clip(word)
    yield clip
