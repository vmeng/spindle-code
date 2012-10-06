from spindle.models import Item, Clip, Speaker
from django.contrib import admin

class ClipInline(admin.TabularInline):
    model = Clip

class SpeakerInline(admin.TabularInline):
    model = Speaker

class ItemAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'audio_url', 'video_url', 'published', 'keywords']})
    ]
    inlines = [SpeakerInline, ClipInline]
    list_display = ('name', 'published')
    search_fields = ('name', 'audio_url', 'video_url')
    date_hierarchy = 'published'
    save_on_top = True

admin.site.register(Item, ItemAdmin)
