from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

import xml.etree.ElementTree as ET

from spindle.models import Track
import spindle.writers.vtt

# Return XML transcript
@login_required
def xml(req, track_id):       
    track = get_object_or_404(Track, pk=track_id)

    transcript = ET.Element('transcript')
    para = ET.SubElement(transcript, 'p')
    
    for clip in track.clip_set.all():
        # Begin new paragraph if indicated
        if clip.begin_para:
            para = ET.SubElement(transcript, 'p')
            
            c = ET.SubElement(para, 'clip')
            for attr in ['intime', 'outtime', 'edited', 'id']:
                c.attrib[attr] = str(clip.__getattribute__(attr))
            c.text = clip.caption_text

    return HttpResponse(ET.tostring(transcript), mimetype="application/xml")

# Return VTT transcript
@login_required
def vtt(req, track_id): 
    track = get_object_or_404(Track, pk=track_id)
    resp = HttpResponse(mimetype="text/vtt")
    track.write_vtt(resp)
    return resp
    
# Return plain text transcript
@login_required
def plaintext(req, track_id):
    track = get_object_or_404(Track, pk=track_id)
    resp = HttpResponse(mimetype="text/plain")
    track.write_plaintext(resp)
    return resp

# Return HTML transcript
@login_required
def html(req, track_id):       
    track = get_object_or_404(Track, pk=track_id)
    resp = HttpResponse('')
    track.write_html(resp)
    return resp
