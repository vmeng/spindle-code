
from math import floor

def secondsToVTT(secs):
    milli = int(1000 * (secs - floor(secs)))
    secs = floor(secs)

    minutes = int(floor(secs/60))
    secs = int(secs - 60*minutes)

    hours = int(floor(minutes/60))
    minutes = int(minutes - 60*hours)

    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, secs, milli)


def write(clips, file_or_name):
    if isinstance(file_or_name, str):
        output = open(output, 'w')
        close = True
    else:
        output = file_or_name
        close = False

    output.write("WEBVTT FILE\n\n")

    count = 1
    for clip in clips:
        output.write("{:d}\n".format(count))
        output.write("{} --> {}\n".format(
                secondsToVTT(clip.intime),
                secondsToVTT(clip.outtime)))
        output.write("{}\n\n".format(clip.caption_text))
        count += 1

    if close: output.close()
