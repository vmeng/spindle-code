# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Item'
        db.create_table('spindle_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('video_url', self.gf('django.db.models.fields.URLField')(max_length=1000, blank=True)),
            ('audio_url', self.gf('django.db.models.fields.URLField')(max_length=1000, blank=True)),
            ('duration', self.gf('django.db.models.fields.IntegerField')()),
            ('published', self.gf('django.db.models.fields.DateTimeField')()),
            ('keywords', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('video_guid', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('audio_guid', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('licence_long_string', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('spindle', ['Item'])

        # Adding model 'ArchivedItem'
        db.create_table('spindle_archiveditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='versions', to=orm['spindle.Item'])),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('spindle', ['ArchivedItem'])

        # Adding model 'TranscriptionTask'
        db.create_table('spindle_transcriptiontask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['spindle.Item'])),
            ('task_id', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('engine', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('spindle', ['TranscriptionTask'])

        # Adding model 'Track'
        db.create_table('spindle_track', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['spindle.Item'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('kind', self.gf('django.db.models.fields.CharField')(default='captions', max_length=10)),
            ('lang', self.gf('django.db.models.fields.CharField')(default='en', max_length=7)),
        ))
        db.send_create_signal('spindle', ['Track'])

        # Adding model 'Speaker'
        db.create_table('spindle_speaker', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('track', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['spindle.Track'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('spindle', ['Speaker'])

        # Adding model 'Clip'
        db.create_table('spindle_clip', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('track', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['spindle.Track'])),
            ('intime', self.gf('django.db.models.fields.FloatField')()),
            ('outtime', self.gf('django.db.models.fields.FloatField')()),
            ('caption_text', self.gf('django.db.models.fields.TextField')()),
            ('edited', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('speaker', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['spindle.Speaker'], null=True, blank=True)),
            ('begin_para', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('spindle', ['Clip'])


    def backwards(self, orm):
        # Deleting model 'Item'
        db.delete_table('spindle_item')

        # Deleting model 'ArchivedItem'
        db.delete_table('spindle_archiveditem')

        # Deleting model 'TranscriptionTask'
        db.delete_table('spindle_transcriptiontask')

        # Deleting model 'Track'
        db.delete_table('spindle_track')

        # Deleting model 'Speaker'
        db.delete_table('spindle_speaker')

        # Deleting model 'Clip'
        db.delete_table('spindle_clip')


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
            'audio_guid': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'audio_url': ('django.db.models.fields.URLField', [], {'max_length': '1000', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'licence_long_string': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
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
            'kind': ('django.db.models.fields.CharField', [], {'default': "'captions'", 'max_length': '10'}),
            'lang': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '7'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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