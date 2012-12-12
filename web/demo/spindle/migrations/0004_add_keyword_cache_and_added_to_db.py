# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Track.updated'
        db.add_column('spindle_track', 'updated',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, default=datetime.datetime(2012, 12, 12, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'Track.keyword_cache'
        db.add_column('spindle_track', 'keyword_cache',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'Track.keyword_cache_date'
        db.add_column('spindle_track', 'keyword_cache_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Item.added_to_db'
        db.add_column('spindle_item', 'added_to_db',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2012, 12, 12, 0, 0), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Track.updated'
        db.delete_column('spindle_track', 'updated')

        # Deleting field 'Track.keyword_cache'
        db.delete_column('spindle_track', 'keyword_cache')

        # Deleting field 'Track.keyword_cache_date'
        db.delete_column('spindle_track', 'keyword_cache_date')

        # Deleting field 'Item.added_to_db'
        db.delete_column('spindle_item', 'added_to_db')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'spindle.archiveditem': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'ArchivedItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['spindle.Item']"}),
            'json': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'spindle.clip': {
            'Meta': {'ordering': "['intime']", 'object_name': 'Clip'},
            'begin_para': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'caption_text': ('django.db.models.fields.TextField', [], {}),
            'edited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intime': ('django.db.models.fields.FloatField', [], {}),
            'outtime': ('django.db.models.fields.FloatField', [], {}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spindle.Speaker']", 'null': 'True', 'blank': 'True'}),
            'track': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spindle.Track']"})
        },
        'spindle.item': {
            'Meta': {'object_name': 'Item'},
            'added_to_db': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'audio_guid': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'audio_url': ('django.db.models.fields.URLField', [], {'max_length': '1000', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'licence_long_string': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'published': ('django.db.models.fields.DateTimeField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'video_guid': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'video_url': ('django.db.models.fields.URLField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'spindle.speaker': {
            'Meta': {'object_name': 'Speaker'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'track': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spindle.Track']"})
        },
        'spindle.track': {
            'Meta': {'object_name': 'Track'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spindle.Item']"}),
            'keyword_cache': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'keyword_cache_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'captions'", 'max_length': '10'}),
            'lang': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '7'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Transcript'", 'max_length': '1000', 'blank': 'True'}),
            'publish_text': ('django.db.models.fields.CharField', [], {'default': "'hidden'", 'max_length': '6'}),
            'publish_transcript': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '6'}),
            'publish_vtt': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '6'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'spindle.transcriptiontask': {
            'Meta': {'object_name': 'TranscriptionTask'},
            'engine': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spindle.Item']"}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['spindle']