
import tempfile
import requests
import subprocess
import os

from django.conf import settings

from . import reader


# Dummy logging function
def echo(*args):
    for arg in args:
        print arg

#
# Step 1: download an MPEG and transcode it to 16k WAV for processing
# by Sphinx
#
def transcode(url, current_task=None, log=echo): 
    state="Downloading '{}' ...".format(url)
    log(state)
    if current_task:
        current_task.update_state(
            state='DOWNLOADING',
            meta={'url': url}
            )
    request = requests.get(url)
    request.raise_for_status()
    log("... downloaded ok")

    infile = tempfile.NamedTemporaryFile()
    log("Saving '{}' to '{}'...".format(url, infile.name))
    infile.write(request.content)
    log("... saved ok")

    wavfile = tempfile.NamedTemporaryFile()
    state="Transcoding to WAV file '{}'".format(wavfile.name)
    log(state)
    if current_task:
        current_task.update_state(
            state='TRANSCODING',
            meta={'url': url, 'wavfile': wavfile.name}
            )

    errcode = subprocess.call([
            'ffmpeg',
            '-i', infile.name, # read input file
            '-y',              # overwrite output file
            '-vn',             # no video
            '-f', 'wav',       # make a WAV file
            '-ar', '16000',    # 16k sampling rate
            '-ac', '1',        # mono audio
            wavfile.name])     # output file
    if errcode:
        raise Exception("Error in FFMPEG: {}".format(errcode))

    log("... transcoding ok")
    return infile, wavfile

#
# Step 2: Take the WAV file and transcribe using Sphinx, yielding clips
#
def transcribe_wavfile(wavfile, log=echo):
    try:
        tmp_dir = settings.SPINDLE_SPHINX_OUTPUT_DIRECTORY or tempfile.tempdir
    except AttributeError:
        tmp_dir = tempfile.tempdir
        
    try:
        sphinx_dir = settings.SPINDLE_SPHINX_DIRECTORY
        if not sphinx_dir: raise AttributeError
    except AttributeError:
        raise Exception("SPINDLE_SPHINX_DIRECTORY is empty or not set in settings.py")
            
    script_fd, script_path = tempfile.mkstemp(prefix="script.", dir=tmp_dir)
    log_fd, log_path = tempfile.mkstemp(prefix="log.", dir=tmp_dir)

    scriptfile = os.fdopen(script_fd, 'w')
    logfile = os.fdopen(log_fd, 'w')

    log("Logging Sphinx info in '{}'".format(log_path))
    log("Saving Sphinx output in '{}'".format(script_path))

    sphinx = subprocess.Popen([
            'java',
            '-mx800m',         # needs 800MB of heap
            '-jar', 'bin/Transcriber.jar',
            wavfile.name],
            cwd=sphinx_dir,
            stdout=subprocess.PIPE,
            stderr=logfile)

    lines = tee(process_readline(sphinx), scriptfile)
    clips = reader.read_clips(lines)

    for clip in clips:        
        yield clip

    if sphinx.returncode:
        raise Exception("Error in Sphinx process: {}".format(sphinx.returncode))

    log("... transcription ok")


# Utility: use the output of a process as a generator, yielding one
# line at a time until process exits
def process_readline(proc):
    while proc.poll() is None:
        line = proc.stdout.readline()
        if line:                #  FIXME: what about blank lines?
            yield line

# Utility: debug a generator by tracing each item
def trace(gen):
    for item in gen:
        print item
        yield item

# Utility: dump lines to a file and pass them along
def tee(source, outfile):
    for line in source:
        outfile.write(line)
        outfile.flush()
        yield line                                
