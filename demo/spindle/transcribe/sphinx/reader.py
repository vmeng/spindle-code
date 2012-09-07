# Simple reader for output from Sphinx4 bin/transcriber.jar

import re
from itertools import ifilter, dropwhile, takewhile
from spindle.models import Clip
from spindle.readers.wordstoclips import clips as words_to_clips


class SphinxToken():
    def __init__(self, token, begin, end):
        self.token = token
        self.begin = begin
        self.end = end

    def __repr__(self):
        return "<SphinxToken: {}({},{})>".format(
            self.token, self.begin, self.end)

tokenRE = re.compile(r'([^(]*)\(([\d.]*),([\d.]*)\)\s*')
def read_tokens(input):
    """
    Generator for tokenizing Sphinx4 output.

    INPUT can be a file, or any other object which can be iterated
    over to produce lines.

    Yields SphinxToken objects where token is the word, or one of the
    special tokens <sil> (silence) or <s> (segment boundary).
    """

    for line in input:
        if re.match('^Falling back', line): continue

        pos = 0
        match = re.match(tokenRE, line)
                      
        while match:
            token, begin, end = match.group(1), \
               float(match.group(2)), float(match.group(3))
            pos += len(match.group(0))
            
            yield SphinxToken(token, begin, end)
            match = re.match(tokenRE, line[pos:])

def remove_silences(tokens):
    """Filter out <sil> silence tokens from `tokens`"""
    return ifilter(lambda t: t.token != '<sil>', tokens)

def one_segment(tokens):
    """Iterate over the first segment in `tokens`, then stop.
    
    `tokens' is an iterator of tokens, as returned by read_tokens().

    Iterating the returned generator discards any <s> tokens at the
    beginning of `tokens', then consumes and yields tokens up to and
    including the next <s> segmentation token.
    """
    return takewhile(lambda t: t.token != '<s>',
                     dropwhile(lambda t: t.token == '<s>',
                               tokens))

def segments(tokens):
    """Iterate over all segments in `tokens'.

    Yields lists of tokens."""
    segment = list(one_segment(tokens))
    while segment:
        yield segment
        segment = list(one_segment(tokens))
    
def token_to_word(token):       # FIXME
    return dict(startTime = token.begin,
                duration = token.end - token.begin,
                name = token.token)

def read_clips(input, **kwargs):
    """Read Sphinx4 output and segment into clips.

    `input' should be a file object, or anything that can be iterated
    to produce lines of text.

    Any keyword arguments are passed unchanged to words_to_clips.

    Yields Clip objects segmented in two ways:

    (1) Sphinx segment tokens <s> begin a new clip

    (2) Within Sphinx segments, words are split into clips using
    words_to_clips. Without additional arguments, each clip will be
    limited to a maximum length of 4 seconds."""
    for segment in segments(remove_silences(read_tokens(input))):
        for clip in words_to_clips(map(token_to_word, segment),
                                   **kwargs):
            yield clip
