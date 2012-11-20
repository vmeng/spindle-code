from django.conf.urls import patterns, include, url
from spindle.rest_api import api_urls
import spindle.views

#
# Routes for views
#
urlpatterns = patterns(
    'spindle.views',

    # Item list
    url(r'^$', 'itemlist', name='spindle_home'),

    # Item-level operations
    url(r'^item/new/', 'new', name='spindle_new'),
    
    url(r'^item/(?P<item_id>\d+)/$', 'item_tracks',
        name='spindle_item_tracks'),
    url(r'^item/(?P<item_id>\d+)/meta/$', 'item_metadata',
        name='spindle_item_metadata'),
    url(r'^item/(?P<item_id>\d+)/revisions/$', 'item_revisions',
        name='spindle_item_revisions'),
    url(r'^item/(?P<item_id>\d+)/add/$', 'item_add_track',
        name='spindle_item_add_track'),

    url(r'^item/revert/(?P<version_id>\d+)/$',
        'revert_item', name='spindle_revert_item'),
    url(r'^item/diff/(?P<version_id>\d+)/$',
        'diff_item', name='spindle_diff_item'),

    # Track-level operations
    url(r'^track/(?P<track_id>\d+)/$', 
        'edit_track', name='spindle_edit'),
    url(r'^track/(?P<track_id>\d+)/meta/$',
        spindle.views.TrackMetaView.as_view(),
        name='spindle_track_meta'),
    
    url(r'^track/(?P<track_id>\d+)/keywords/$',
        'keywords', name='spindle_track_keywords'),

    # Tasks: importing, publishing, etc.
    url(r'^scrape/', 'scrape', name='spindle_scrape'),
    url(r'^publish/', 'publish', name='spindle_publish'),

    # Transcription queue
    url(r'^queue/$', 'queue', name='spindle_queue'),
    )

# Partial views for ajax updating
urlpatterns += patterns(
    'spindle.views',
    url(r'^a/p/queue$', 'queuepartial'),

    url(r'tasks/(?P<task_id>[^/]+)$', 'task_info')
)

# Export formats
urlpatterns += patterns(
    'spindle.export_views',

    # Export transcript formats
    url(r'track/(?P<track_id>\d+)/xml/$', 'xml', name='spindle_export_xml'),
    url(r'track/(?P<track_id>\d+)/html/$', 'html', name='spindle_export_html'),
    url(r'track/(?P<track_id>\d+)/vtt/$', 'vtt', name='spindle_export_vtt'),
    url(r'track/(?P<track_id>\d+)/text/$', 'plaintext', name='spindle_export_text')
    )

# REST api
urlpatterns += patterns('',
    (r'^spindle/REST/', include(api_urls)),
)

