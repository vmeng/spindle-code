# Brute simple REST api for the spindle caption editor

import json
from functools import wraps

from django.conf.urls import patterns, include, url
from django.shortcuts import get_object_or_404, redirect, render
from django.db import models
from django.db import transaction
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic.base import View
from django.utils.decorators import method_decorator

from spindle.models import Item, Track, Speaker, Clip


def json_response(objs):
    return HttpResponse(serializers.serialize('json', objs),
                        content_type='application/json')

def json_login_required(view):
    @wraps(view)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated():
            return view(request, *args, **kwargs)

        return HttpResponse(json.dumps({ 'status': 'error',
                                         'error': 'Not authenticated.' }),
                            mimetype = 'application/json',
                            status = 403)
    return wrap
    

# Two simple generic resource classes: single item and list of items
class SingleResource(View):
    model = None

    @method_decorator(json_login_required)
    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(self.model, pk = kwargs['pk'])
        return super(SingleResource, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return json_response([self.object])
    
    def field_editable(self, key):
        if key[-3:] == "_id":
            return self.model._meta.get_field_by_name(key[:-3])[0].editable
        else:
            return self.model._meta.get_field_by_name(key)[0].editable

    def put(self, request, *args, **kwargs):
        data = json.loads(request.body)
        del data['pk']

        with transaction.commit_on_success():
            for key, value in data.iteritems():
                if self.field_editable(key):
                    setattr(self.object, key, value)
                    self.object.save()

        return json_response([self.object])
    
class CollectionResource(View):
    model = None

    @method_decorator(json_login_required)
    def dispatch(self, request, *args, **kwargs):
        self.query_set = self.get_query_set(request, *args, **kwargs)
        return super(CollectionResource, self).dispatch(request, *args, **kwargs)

    def get_query_set(self, *args, **kwargs):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        return json_response(self.query_set)
      
    def put(self, request, *args, **kwargs):
        data = map(self.parse, json.loads(request.body))
        model = self.model
        response = []

        with transaction.commit_on_success():
            self.query_set.delete()

            for fields in data:
                obj = model(**fields) 
                obj.save()
                response.append(obj)
        return json_response(response)
    
    def parse(self, data):
        return data

    def post(self, request, *args, **kwargs):
        data = self.parse(json.loads(request.body))
        for field in ('pk', self.model._meta.pk.name):
            if field in data: del data[field]

        with transaction.commit_on_success():
            self.object = self.model(**data)
            self.object.save()

        return json_response([self.object])



# The model-backed resources  
class ItemResource(SingleResource):
    model = Item

class TrackResource(SingleResource):
    model = Track
        
class TrackSpeakersResource(CollectionResource):
    model = Speaker
    def get_query_set(self, request, pk=None):
        self.track = get_object_or_404(Track, pk=pk)
        return self.track.speaker_set.all()

    def parse(self, data):
        data['track_id'] = self.track.id
        return data

class TrackClipsResource(CollectionResource):
    model = Clip
    def get_query_set(self, request, pk=None):
        self.track = get_object_or_404(Track, pk=pk)
        return self.track.clip_set.all()

    def parse(self, data):
        data['track_id'] = self.track.id
        return data

# class SpeakerResource(SingleResource):
#     model = Speaker
    
# class ClipResource(SingleResource):
#     model = Clip


api_urls = patterns(
    '',
  
    url(r'^track/(?P<pk>\d+)/$', TrackResource.as_view()),
    url(r'^track/(?P<pk>\d+)/speakers/$', TrackSpeakersResource.as_view()),
    url(r'^track/(?P<pk>\d+)/clips/$', TrackClipsResource.as_view()),

    url(r'^item/(?P<pk>\d+)/$', ItemResource.as_view()),
    # url(r'^clip/(?P<pk>\d+)/$', ClipResource.as_view()),
    # url(r'^speaker/(?P<pk>\d+)/$', SpeakerResource.as_view()),
)
