from spindle.models import Clip
import re

# A crude reader for VTT/SRT format files

onFirstLine = 0
onSeparator = 4
onIdLine = 1
onTimecodeLine = 2
onTextLine = 3

timecodeRE = re.compile(r'(\d+):(\d+)\:(\d+)[.,](\d+) --> (\d+):(\d+)\:(\d+)[.,](\d+)')

class VTTReader:    
    def __init__(self):
        self.state = onFirstLine

        self.clip = Clip()
        self.lines = []
        self.clips = []

    def parse(self, file):
        for line in file:
            self.handle(line.strip())
        return self.clips

    def handle(self, line):
        if self.state == onFirstLine:
            if line == 'WEBVTT FILE':
                self.state = onSeparator
            else:
                self.state = onSeparator
                self.handle(line)

        elif self.state == onSeparator: 
            if line != '':
                self.state = onIdLine
                self.handle(line);

        elif self.state == onIdLine:
            self.state = onTimecodeLine            

        elif self.state == onTimecodeLine:
            codes = parseVTTTimecodes(line)
            self.clip.intime = codes['intime']
            self.clip.outtime = codes['outtime']
            self.state = onTextLine

        elif self.state == onTextLine:
            if line == '':
                self.clip.caption_text = ''.join(self.lines)
                self.clips.append(self.clip)

                self.lines = []
                self.clip = Clip()

                self.state = onSeparator
            else:                
                self.lines.append(line)

def parseVTTTimecodes(line):
    def toTimecode(hr, min, sec, milli):
        return float(milli) / 1000 + int(sec) + 60 * (int(min) + 60 * int(hr))

    match = timecodeRE.match(line)
    if not match:
        return dict(intime=0, outtime=0) # FIXME
    else:        
        return dict(intime=toTimecode(match.group(1),
                                      match.group(2),
                                      match.group(3),
                                      match.group(4)),
                    outtime=toTimecode(match.group(5),
                                       match.group(6),
                                       match.group(7),
                                       match.group(8)))

def read(vtt):
    r = VTTReader()
    if(isinstance(vtt, str)):
        f = open(vtt)
    else:
        f = vtt

    return r.parse(f)
    
