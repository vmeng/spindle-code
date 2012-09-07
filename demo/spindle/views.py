from pprint import pprint
import json, re
import xml.etree.ElementTree as ET

from django.template import Context, loader, RequestContext
from django.utils import timezone
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django import forms
from django.forms import ModelForm
from django.db.models import Q
from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.edit import UpdateView
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import update_object

from spindle.models import Item, ArchivedItem, Track, TranscriptionTask
from spindle.readers import feedscraper, vtt, xmp
import spindle.keywords.collocations as collocations
import spindle.transcribe

import spindle.transcribe.koemei as koemei
import spindle.transcribe.sphinx as sphinx



# List items for transcription
@login_required
def itemlist(request):
    query = request.GET

    # Find search parameters from query, or set defaults
    limit = int(query['limit']) if 'limit' in query else 15
    offset = int(query['offset']) if 'offset' in query else 0
    search = query['search'] if ('search' in query and len(query['search'])) else None
    
    order_column = query['sortby'] if 'sortby' in query else 'published'
    order_direction = int(query['sortdir']) if 'sortdir' in query else -1
    
    # Construct the base search, without range slicing
    def base_query():
        if search:
            return Item.objects.filter(
                Q(name__icontains=search) |
                Q(audio_url__icontains=search) |
                Q(video_url__icontains=search))
        else:
            return Item.objects.all()

    # Sort
    if order_column == 'edited_fraction':
        # Django doesn't have an aggregate function to take the ratio
        # of edited clips to total clips, so we have to sort in Python
        query = Item.objects.annotate_counts(base_query())
        query = query.filter(clip_count__gt=0)
        count = query.count()
        items = sorted(query, key=Item.edited_fraction, reverse=True)        
        items = items[offset:offset+limit]
    else:
        count = base_query().count()        
        query = base_query().order_by(
            order_column if order_direction > 0 else "-" + order_column)
#        query = Item.objects.annotate_counts(query)
        items = query[offset:offset+limit]
    

    # Count and slice

    # Construct readable descriptions of search and range
    if len(items) < limit:
        rangeDescription = "all"
    else:
        rangeDescription = "{} to {} of ".format(
            offset+1,
            min(offset+limit, count))
    searchDescription = "containing '{}'".format(search) if search else "in database"
    
    # Construct URLs for changing slice and sorting methods
    baseURL = '?'
    baseParams = QueryDict('').copy()
    baseParams.update({ 'search': search if search else '',
                        'sortby': order_column,
                        'sortdir': order_direction,
                        'limit': limit })

    nextParams = baseParams.copy()
    prevParams = baseParams.copy()

    nextParams.update({ 'offset': min(offset + limit, count - 1) })
    prevParams.update({ 'offset': max(offset - limit, 0) })
                          
    nextUrl = baseURL + nextParams.urlencode()
    prevUrl = baseURL + prevParams.urlencode()

    orderUrls = {};
    for col in ['item_id', 'name', 'video_url',
                'media_type', 'duration', 'published',
                'edited_fraction']:
        params = baseParams.copy()

        if(col != order_column):
            del params['sortby']
            params.update({ 'sortby': col })
        else:
            del params['sortdir']
            params.update({ 'sortdir': -order_direction })

        orderUrls[col] = baseURL + params.urlencode()
    
    # Render template
    return render(request, 'spindle/itemlist.html', {
            'title': "Item list",
            'items': items,
            
            'range': rangeDescription,
            'count': count,
            'searchdescription': searchDescription,
            
            'search': search if search else '',
            'nextUrl': nextUrl,
            'prevUrl': prevUrl,
            'orderUrls': orderUrls,                                   
            })



# Item-level operations

# Item metadata form
class ItemMetadataForm(ModelForm):
    class Meta:
        model = Item
        fields = ('name', 'audio_url', 'video_url', 'keywords')

# New item form
@login_required
def new(request):
    if request.method == 'POST':
        form = ItemMetadataForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            if 'caption_file' in data: del data['caption_file']

            item = Item(**data)
            item.duration = 0   #  FIXME
            item.published = timezone.now()
            item.save()

            return redirect(item_tracks, item_id=item.id)
    else:
        form = ItemMetadataForm()

    return render(request, 'spindle/new.html', {
        'form': form,
        'rss_url': settings.SPINDLE_SCRAPE_RSS_URL
        })

# Scrape RSS for new items

# FIXME: This should run as a task and the page should poll via AJAX
# instead of blocking like this.
@login_required
def scrape(request):
    import spindle.tasks
    spindle.tasks.scrape()
    return redirect('spindle_home')


# File upload form
UPLOAD_FILE_TYPES = (('xmp', 'XMP (Adobe Premiere) file'),
                     ('srt', 'SRT/WebVTT file'),
                     ('koemei', 'Koemei XML transcript'),
                     ('sphinx', 'Raw Sphinx output'))                     
class UploadTrackForm(forms.Form):
    file_type = forms.ChoiceField(choices=UPLOAD_FILE_TYPES)
    caption_file = forms.FileField(required=True)

# Request transcription form
TRANSCRIPTION_ENGINES = [(key, engine['name'])
                         for key, engine
                         in spindle.transcribe.engine_map.iteritems()]
class RequestTranscriptForm(forms.Form):
    engine = forms.ChoiceField(choices=TRANSCRIPTION_ENGINES)

# List item transcripts
@login_required
def item_tracks(request, item_id):
    return object_detail(
        request,
        queryset = Item.objects,
        object_id = item_id,
        template_name = "spindle/item_tracks.html",
        template_object_name = "item")

@login_required
def item_revisions(request, item_id):
    return object_detail(
        request, queryset = Item.objects, object_id = item_id,
        template_name = "spindle/item_revisions.html",
        template_object_name = "item")

@login_required
def item_metadata(request, item_id):
    return update_object(request,
        form_class = ItemMetadataForm,
        object_id = item_id,
        template_name = "spindle/item_metadata.html",
        template_object_name = "item",
        post_save_redirect = reverse(item_metadata, kwargs={'item_id': item_id}))

@login_required
def item_add_track(request, item_id):
    item = get_object_or_404(Item, pk=item_id)    
    new_track_form = upload_track_form = request_transcript_form = None

    if 'new_track' in request.POST:
        new_track_form = TrackMetadataForm(request.POST)        
        if new_track_form.is_valid():
            data = new_track_form.cleaned_data
            track = Track(item=item, **data)
            track.save()
            return redirect(edit_track, track_id=track.id)
    elif 'upload_track' in request.POST:
        upload_track_form = UploadTrackForm(request.POST, request.FILES)
        if upload_track_form.is_valid():
            data = upload_track_form.cleaned_data
            file_type = data['file_type']
            upload = request.FILES['caption_file']
            
            if file_type == 'srt':            
                script = vtt.read(upload)                    
            elif file_type == 'xmp':
                script = xmp.read(upload)
            elif file_type == 'koemei':
                xml = ET.parse(upload)
                objects = koemei.reader.read(xml)
                script = objects['speakers']
                script.extend(objects['clips'])
            else:
                raise Exception('Unrecognised caption file format')
            
            track = Track(item=item, name=upload.name)
            track.save()
            for obj in script:
                obj.track = track
                obj.save()
        return redirect(edit_track, track_id=track.id)
    elif 'request_transcript' in request.POST:
        request_transcript_form = RequestTranscriptForm(request.POST)
        if request_transcript_form.is_valid():
            engine = request_transcript_form.cleaned_data['engine']
            if engine not in spindle.transcribe.engine_map:
                raise Exception(u"Bad value for engine: {}".format(engine))
            
            item.request_transcription(engine)
            return redirect('spindle_queue')

    if new_track_form is None: new_track_form = TrackMetadataForm()
    if upload_track_form is None: upload_track_form = UploadTrackForm()
    if request_transcript_form is None: request_transcript_form = RequestTranscriptForm()
    
    return render(request, 'spindle/item_add_transcript.html', {
            'item': item,
            'new_track_form': new_track_form,
            'upload_track_form': upload_track_form,
            'request_transcript_form': request_transcript_form,
            })

# Version control
@require_POST
@login_required
def revert_item(request, version_id):
    version = get_object_or_404(ArchivedItem, pk=version_id)

    version.revert()
    return redirect(item_tracks, item_id=version.item.id)

@login_required
def diff_item(request, version_id):
    version = get_object_or_404(ArchivedItem, pk=version_id)

    diff_file = version.diff()
    resp = HttpResponse('', content_type='text/plain')
    for line in diff_file: resp.write(line)
    return resp


# Track-level operations

# Edit track
@login_required
def edit_track(request, track_id):
    track = get_object_or_404(Track, pk=track_id)
    item = track.item

    return render(request, 'spindle/edit.html', {
            'item': item,
            'track': track,
            })
# Track metadata
class TrackMetadataForm(ModelForm):
    class Meta:
        model = Track
        fields = ('name', 'kind', 'lang',
                  'publish_text', 'publish_vtt', 'publish_transcript')
        
class TrackMetaView(UpdateView):
    model = Track
    template_name = "spindle/track_meta.html"
    form_class = TrackMetadataForm
    pk_url_kwarg = 'track_id'
    template_object_name = 'track'

    def get_success_url(self, **kwargs):
        return reverse('spindle_track_meta', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrackMetaView, self).get_context_data(**kwargs)
        context['item'] = context['track'].item
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TrackMetaView, self).dispatch(*args, **kwargs)

# Display keywords
@login_required
def keywords(request, track_id):
    track = get_object_or_404(Track, pk=track_id)
    item = track.item
    text = (clip.caption_text for clip in track.clip_set.all())
    kw, ngrams = collocations.keywords_and_ngrams(text)
             
    def keyword_html(sorted_x):
        tags = ""
        for (word, ll) in sorted_x[0:100]:
            # Word size determined by log likelihood
            # only using 5 classes but we could follow wikipedia tag cloud equation 
            # using tmax and tmin to determine the classes, ignored at the moment
            # until we know what we want as output
            size = int(ll / 20)
            if size > 4:
                size = 4
            tags += '<a href="#" class="tag c{}">{}</a> '.format(size, word)
        return tags

    def ngram_html(ngrams):
        tags = ""
        # scale = max(n for _, n in ngrams) if ngrams else 0

        for ((w1, w2), n) in reversed(ngrams):
            size = 4            # 4 * int(n / scale)
            tags += '<a href="#" class="tag c{}">{} {}</a> '.format(size, w1, w2)
        return tags

    return render(request, 'spindle/keywords.html', {
            'title': u"Keywords: '{}'".format(item.name),
            'item': item,
            'track': track,
            'keywordblock': keyword_html(kw),
            'ngramblock': ngram_html(ngrams),
            'oxitems_keywords': item.keywords
            })
 

# Transcription queue
@login_required
def queue(request):
    return render(request, 'spindle/queue.html', {
            'title': "Transcription queue",
            'queue': get_queue()
            })

@login_required
def queuepartial(request):
    return render(request, 'spindle/queuepartial.html', {
            'queue': get_queue()
            })

def get_queue():
    def sort_key(req):
        try: 
            return ['PROGRESS',
                    'DOWNLOADING',
                    'TRANSCODING',
                    'PENDING',
                    'SUCCESS',                    
                    'FAILURE'].index(req['task'].status())
        except ValueError:
            return 0

    def format_status(task):
        if task.status() == 'PROGRESS':
            return "{}% complete".format(int(task.result()['progress'] * 100))
        else:
            try:
                return {'PENDING' : "Queued",
                        'DOWNLOADING' : 'Fetching media',
                        'TRANSCODING' : 'Converting audio',
                        'SUCCESS' : "Finished",
                        'FAILURE' : "Error"}[task.status()]
            except KeyError:
                return "Unknown" 
        
    queue = []
    for task in TranscriptionTask.queue.all():
        req = dict(task=task, item=task.item)
        queue.append(req)

        req['raw_status'] = task.status()
        req['status'] = format_status(task)
        try:
            req['engine'] = spindle.transcribe.engine_map[task.engine]['name']
        except:
            req['engine'] = ''

        if task.status() == 'PROGRESS' or task.status() == 'RUNNING': # FIXME
            req['eta'] = task.result['eta']
            req['progress_bar'] = True
            req['percent'] = int(task.result()['progress'] * 100)

    return sorted(queue, key=sort_key)
