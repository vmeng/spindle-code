# Simple reader for Koemei XML output format

import xml.etree.ElementTree as ET
from spindle.models import Speaker, Clip
from spindle.readers.wordstoclips import clips as words_to_clips


def read(xml, max_time=4, max_words=None):
    """
    Transform XML, an ElementTree.Element representation of Koemei's
    <segmentation> output, into a series of spindle clips and associated
    speaker objects.

    Returns a dict with two values: CLIPS and SPEAKERS
    """
    speakers = dict()
    clips = []
    for segment in xml.findall('segment'):
        start        = float(segment.find('start').text.strip()) / 100
        end          = float(segment.find('end').text.strip()) / 100
        speaker_name = segment.find('speaker').text.strip()
        try:
            speaker = speakers[speaker_name]
        except KeyError:
            speaker = Speaker(name=speaker_name)
            speakers[speaker_name] = speaker

        segment_clips = words_to_clips(segment_to_words(segment),
                                       max_time=max_time,
                                       max_words=max_words,
                                       speaker=speaker)
        clip = segment_clips.next()
        clip.begin_para = True
        clips.append(clip)
        for clip in segment_clips: clips.append(clip)

    return dict(clips=clips, speakers=speakers.values())
                
                
def segment_to_words(segment):
    """
    Generator that reads the contents of SEGMENT, an
    ElementTree.Element representation of a Koemei <segment>, and
    yields timecoded words, represented as dictionaries with values
    for 'startTime', 'duration' and 'name'.
    """
    for label_seq in segment.findall('label-seq'):
        for label in label_seq.findall('label'):
            start = float(label.find('start').text.strip()) / 100
            end   = float(label.find('end').text.strip()) / 100
            value = label.find('value').text.strip()
            yield dict(startTime = start,
                       duration  = end - start,
                       name      = value)
            
            

