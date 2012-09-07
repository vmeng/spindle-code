#
# The Sphinx reader and the XMP reader both produce streams of
# timecoded "words" as dictionaries with "startTime", "duration", and
# "name" properties. This module makes clips from words by joining
# together words up to a maximum duration per clip (TODO: or maximum
# text length per clip )
#

import spindle.models

def clips(words, max_time=4, max_words=None, speaker=None):
    def start_clip(word):
        return spindle.models.Clip(
            intime = word['startTime'],
            outtime = word['startTime'] + word['duration'],
            caption_text = word['name'],
            speaker=speaker)

    words = iter(words)
    word = words.next()
    clip = start_clip(word)

    for word in words:
        end_time = word['startTime'] + word['duration']
        if end_time - clip.intime < max_time:
            clip.caption_text += ' ' + word['name'];
            clip.outtime = word['startTime'] + word['duration']            
        else:                
            yield clip
            clip = start_clip(word)

    yield clip
