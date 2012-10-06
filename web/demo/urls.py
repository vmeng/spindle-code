from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from django.conf.urls.defaults import *
from views import logout_page

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
                       
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', logout_page),

    (r'^', include('spindle.urls')),                                              
)
