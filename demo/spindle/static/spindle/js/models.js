/* -*- js2-additional-externs: ("SPINDLE" "document" "window" "Backbone" "_") -*- */

(function( undefined ) {
    "use strict";
    
    // Backbone.noConflict support. Save local copy of Backbone object.
    var Backbone = window.Backbone;

    Backbone.Model.prototype.idAttribute = 'pk';

    var oldUrl = Backbone.Model.prototype.url;

    Backbone.Model.prototype.url = function() {
        return addSlash(oldUrl.apply(this)) || null;
    };
        
    Backbone.Model.prototype.parse = function( data ) {
        var parseOne = function(data) {
            var fields = _.clone(data.fields);
            fields.pk = data.pk;        
            return fields;
        };

        if(_.isArray(data))
            return parseOne(data[0]);
        else
            return parseOne(data);
    };    

    var addSlash = function( str ) {
	return str + ( ( str.length > 0 && str.charAt( str.length - 1 ) === '/' ) ? '' : '/' );
    };

})();


var Item = Backbone.RelationalModel.extend({
    urlRoot: '/spindle/REST/item',

    relations: [{
        type: Backbone.HasMany,
        key: 'tracks',
        relatedModel: 'Track',
        includeInJSON: false,
        reverseRelation: {
            key: 'item',
            keyDestination: 'item_id',
            includeInJSON: 'pk'
        }
    }]
});

var Track = Backbone.RelationalModel.extend({
    urlRoot: '/spindle/REST/track',    

    relations: [{
        type: Backbone.HasMany,
        key: 'clips',
        relatedModel: 'Clip',
        collectionType: 'ClipSet',
        includeInJSON: false,
        reverseRelation: {
            key: 'track',
            keyDestination: 'track_id',
            includeInJSON: 'pk'
        }
    }, {
        type: Backbone.HasMany,
        key: 'speakers',
        relatedModel: 'Speaker',
        collectionType: 'SpeakerSet',
        includeInJSON: false, 
        reverseRelation: {
            key: 'track',
            keyDestination: 'track_id',
            includeInJSON: 'pk'
        }
    }]
});

var Speaker = Backbone.RelationalModel.extend({
});

var Clip = Backbone.RelationalModel.extend({
    relations: [{
        type: Backbone.HasOne,
        key: 'speaker',
        keyDestination: 'speaker_id',
        relatedModel: 'Speaker',
        includeInJSON: 'pk'
    }]
});

var SyncableCollection = Backbone.Collection.extend({
    save: function (options) {
        var self = this,
            newObjects = this.filter(function (obj) {
                return obj.isNew();
            }),
            counter = 0;
        
        if(!newObjects.length) { 
            bulkSave();
        } else {
            _.each(newObjects, function (obj) {
                obj.save({}, { success: singleSuccess, error: error });
            });
        }

        function singleSuccess(result) {
            counter += 1;
            if(counter == newObjects.length) {                
                bulkSave();
            }
        };
        
        function bulkSave() {
            $.ajax({ type: 'PUT',
                     url: self.url(),
                     processData: false,
                     contentType: 'application/json',
                     data: JSON.stringify(self.toJSON()),
                     success: bulkSuccess,
                     error: error
                   });
        }

        function bulkSuccess(result) {
            _.each(result, function (data) {
                var model = self.model.findOrCreate(data.pk);
                if(model) model.set(model.parse(data));
            });

            self.trigger('sync');
            if(options && _.has(options, 'success')
               && _.isFunction(options.success)) {
                options.success.call(this);
            }
        }

        function error () {
            if(options && _.has(options, 'error')
               && _.isFunction(options.error)) {
                options.error.call(this);
            }
        }
    }
});

var ClipSet = SyncableCollection.extend({
    model: Clip,
    url: function () {
        return this.track && this.track.url() + 'clips/';
    },
    comparator: function(clip) { return clip.get('intime'); }
});

var SpeakerSet = SyncableCollection.extend({
    model: Speaker,
    url: function () {
        return this.track && this.track.url() + 'speakers/';
    }
});

Item.setup();
Track.setup();