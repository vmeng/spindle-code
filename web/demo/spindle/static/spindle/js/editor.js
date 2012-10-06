/* -*- js2-additional-externs: ("SPINDLE" "sprintf" "document" "window") -*- */

/*
 * Class Editor: the caption editor 
 * 
 * Controls a video/audio player. Fetches the clips from the server
 * when loaded and constructs a list of Caption objects to edit them
 * with.
 */
SPINDLE.Editor = function () {
};

/* 
 * Editor properties and instance methods
 */
SPINDLE.Editor.prototype = {
    // References to DOM elements
    player : undefined,         // <video> or <audio> element
    saveButton: undefined,     

    /* How many clips have been edited? */
    editedCount: 0,

    /* Index of currently playing clip
     */
    playIdx: 0,

    /* Flag: Set to the caption ID when we have just jumped to the
     * beginning of a caption, inhibits scrolling & auto-adjusting
     * backwards until the caption changes */
    justSelectedIdx: null,
 
    /* The item we are editing */
    item: undefined,
    

    /**
     * Setup procedures
     */
    init: function () {
        var self = this,
            Editor = SPINDLE.Editor;

        var item = SPINDLE.init.item;
        this.track = SPINDLE.init.track;

        // Set up player
        self.player = $('#player')
            .bind("timeupdate", $.proxy(Editor.callbacks.update, self))
            .get(0);

        self.status("fetching item...");
        item.fetch().success(function () {
            self.status("fetching track...");
            self.track.fetch().success(function () {
                self.status("fetching speakers...");
                self.track.get('speakers').fetch().success(success);
                
                function success () {
                    self.status("fetching clips...");
                    self.track.get('clips').fetch().success(success2);

                    function success2 () {
                        self.status("done!");

                        // Make a default speaker if needed
                        if(!self.track.get('speakers') || !self.track.get('speakers').length) {
                            self.track.set('speakers', new SpeakerSet([{
                                track: self.track,
                                name: "Speaker 1"
                            }]));
                        }

                        // Make empty captions if needed
                        if(self.track.get('clips').length) {
                            self.finishInit();
                        } else {
                            self.makeEmptyClips();
                        }
                    }
                }
            });
            
        });
    },
    
    makeEmptyClips: function () {
        var self = this; 
        
        // We need the duration from the media player before creating
        // empty clips
        if(self.player.duration) {
            makeClips();
        } else {
            self.status('Waiting for media to load...');
            $(self.player).bind('loadedmetadata', makeClips);
        }

        function makeClips() {
            self.status('Creating empty transcript...');
            var intime = 0.0, clip, cliplength = 4.0,
                clipset = new ClipSet();
            
            while (intime < self.player.duration) {
                self.track.get('clips').push({
                    track: self.track,
                    intime: intime,
                    outtime: intime + cliplength,
                    caption_text: "",
                    edited: false 
                });
                intime += cliplength;
            }
            
            self.finishInit();
        }
    },
    
    finishInit: function () {
        var Caption = SPINDLE.Caption,
            Editor = SPINDLE.Editor,
            self = this,
            prevSpeaker = null;

        // Track changes
        self.track.get('speakers').on('change', dirty);
        self.track.get('clips').on('change', dirty);
        self.track.get('clips').on('add', dirty);

        function dirty(obj, changed) {
            obj.dirty = true;
            self.dirty(true);
        }

        // Set up drop down menus
        $('.dropdown-toggle').dropdown();
        $('#speed-menu a').bind('click', function () {
            self.player.playbackRate = Number(($(this).data('speed')));
        });
        
        // Save changes before leaving
        $(window).bind('unload', $.proxy(self.save, self));

        // Create editable caption views
        this.track.get('clips').each(function(clip, i) {
            var isSpeakerChange = (i == 0) || clip.get('speaker') !== prevSpeaker,            
                caption = new Caption(self, clip, false, isSpeakerChange);

            clip.caption = caption;
            $("#captionList").append(caption.dom);
            if(clip.get('edited')) self.editedCount++;

            prevSpeaker = clip.get('speaker');
        });

        // Bind key events, button clicks
        $(document).bind("keydown", $.proxy(Editor.callbacks.keydown, this)); 
        $(".next-unedited").click($.proxy(this.nextUnedited, this));
        $(".prev-unedited").click($.proxy(this.prevUnedited, this));
        $(".export-link").click(Editor.callbacks.exportLink);

        // Grab other DOM elements
        this.saveButton = $('#save-button')
            .click($.proxy(this.save, this))
            .get(0);
        
        // Bind buttons in modal dialogs
        $("#add-speaker-button").click($.proxy(Editor.callbacks.addSpeaker, this));
        $("#rename-speaker-button").click($.proxy(Editor.callbacks.renameSpeaker, this));
        $(this.player).trigger('timeupdate');

        // Update display
        this.updateStats();
    },    

    /*
     * Set/get dirty (edited) flag
     */
    dirty: (function () {
        var dirty = false;

        return function(setTo) {
            if(setTo === undefined)
                return dirty;
            
            dirty = setTo;
            if(dirty) {
                $(this.saveButton).removeClass('disabled');
            } else {
                $(this.saveButton).addClass('disabled');
            }
            
        };
    }()),
    
    /*
     * Functions for manipulating the screen
     */
    status: function (msg) {
        $('#stats').html(msg);    
    },

    redisplay: (function () {
        var oldIdx = null;

        return function () {
            var clip = this.track.get('clips').at(this.playIdx);
        
            if(this.player.currentTime < clip.get('outtime')) {
                $("#caption").html(clip.get('caption_text'));
            } else {
                $("#caption").html("");
            }
            
            if(oldIdx !== null && this.captionAtIdx(oldIdx)) {
                this.captionAtIdx(oldIdx).makeActive(false);            
            }
            this.playCap().makeActive();
            oldIdx = this.playIdx;
        };
    })(),

    scrollto: function () {
        var $list = $('#captionList');
        var scroll = Math.max(0, this.captionPosition(this.playCap())
                              - $list.height() / 2);
        $list.scrollTop(scroll);
    },

    captionPosition: function (caption) {
        var $list = $('#captionList');
        // HACK UGH FIXME
        return $(caption.dom).offset().top
            + $list.scrollTop() - $list.position().top;
    },

    editIdx: function () {
        var active = document.activeElement;
        if(active) {
            var caption = SPINDLE.Caption.fromDOM(active);
            return caption ? this.track.get('clips').indexOf(caption.clip) : null;
          } else {
              return null;
          }
    },

    updateStats: function() {
        var percentage = 100 * this.editedCount / this.track.get('clips').length;
        $("#stats").html(sprintf("%d%% checked (%d of %d captions)",
                                 percentage, this.editedCount,
                                 this.track.get('clips').length));
    },

    playPause: function() {
        if(this.player.paused) {
            this.player.play();
        } else {
            this.player.pause();
            if(this.editIdx() !== null && this.editIdx() <= this.playIdx) {
                this.jumpToIdx(this.editIdx());
            }
        }
    },
    
    /*
     * "Edit speaker" modal dialog stuff.
     */
    // Show the dialog
    editSpeakers: function () {
        this.updateModalDialog();
        $("#edit-speaker-modal").modal();
    },

    // Update the speaker-selection menu of the dialog with current
    // values
    updateModalDialog: function (selected) {
        var self = this, select, option;

        select = $("<select />")
            .attr('id', 'edit-speaker-select');

        if(this.track.get('speakers').length) {
            this.track.get('speakers').each(function(speaker, idx) {
                option = $("<option />")
                    .html(speaker.get('name'))
                    .attr("value", speaker.get('id'))
                    .data("speaker", speaker);
                if(selected && selected === speaker) {
                    option.attr('selected', 'selected');
                }
                select.append(option);
            });
            $('#edit-speaker-name').removeAttr('disabled');
            $('#rename-speaker-button').removeAttr('disabled');
        } else {
            select.attr('disabled', 'disabled');
            $('#edit-speaker-name').attr('disabled', 'disabled');
            $('#rename-speaker-button').attr('disabled', 'disabled');
        }
        
        $("#edit-speaker-select").replaceWith(select);
    },

    // Update the speaker-selection menus of all the Caption elements,
    // after editing
    updateSpeakerSelectors: function () {
        this.track.get('clips').each(function (clip, idx) {
            clip.caption.updateSpeakerSelector();
        });
    },

    /*
     * Jump to clip at given array index
     */
    jumpToIdx: function (idx) {
        this.playIdx = this.justSelectedIdx = idx;
        this.player.currentTime = this.track.get('clips').at(idx).get('intime');
        this.redisplay();
    },

    jumpToClip: function (clip) {
        var idx = this.track.get('clips').indexOf(clip);
        if(idx !== -1) this.jumpToIdx(idx);
    },

    /*
     * Edit the clip at a given index
     */
    editAtIdx: function (idx, nofocus) {
        if(idx !== null) {
            if(!nofocus)
                this.track.get('clips').at(idx).caption.focus();

            if(this.player.paused) {
                this.jumpToIdx(idx);
            }        
        }
    },

    editClip: function (clip, nofocus) {
        var idx = this.track.get('clips').indexOf(clip);
        this.editAtIdx(idx === -1 ? null : idx, nofocus);
    },
    
    clipBefore: function (clip) {
        return this.track.get('clips').at(this.track.get('clips').indexOf(clip) - 1);
    },

    clipAfter: function (clip) {
        return this.track.get('clips').at(this.track.get('clips').indexOf(clip) + 1);
    },
    
    removeClip: function(clip) {
       // this.track.get('clips').splice(this.track.get('clips').indexOf(clip), 1);
        this.track.get('clips').remove(clip);
    },

    insertClipAfter: function(newclip, after) {
       // this.track.get('clips').splice(this.track.get('clips').indexOf(after) + 1, 0, newclip);
        this.track.get('clips').add(newclip);
    },

    /* 
     * Move down or up the list of captions. Behaves differently
     * depending on whether a caption editor is focused or not.
     */
    moveUp: function () {
        if(this.editIdx() !== null && this.editIdx() !== 0) {
            this.editAtIdx(this.editIdx() - 1); 
            if(this.editCap())
                this.editCap().point(this.editCap().text().length);
        } else if(this.playIdx !== 0) {
            this.jumpToIdx(this.playIdx - 1);
            if(this.player.paused) {
                this.scrollto();
            }
        }
    },
    
    moveDown: function () {
        var cap = this.editCap(),
            max = this.track.get('clips').length - 1;
        if(this.editIdx() !== null && this.editIdx() < max) {
            this.editAtIdx(this.editIdx() + 1);
            this.editCap().point(0);
        } else if(this.playIdx < max) {
            this.jumpToIdx(this.playIdx + 1);
            if(this.player.paused) {
                this.scrollto();
            }
        }
    },

    /* 
     * Skip to next un-corrected caption
     */
    skipUnedited: function (dir) {
        var len = this.track.get('clips').length,
            idx = this.playIdx + dir;
        if(idx < 0) idx = 0;
        else if(idx >= len) idx = len - 1;

        for( ; idx >= 0 && idx < len && this.track.get('clips').at(idx).get('edited'); idx += dir);
        this.jumpToIdx(idx);
        this.scrollto();
    },
    nextUnedited: function () { this.skipUnedited(1); },
    prevUnedited: function () { this.skipUnedited(-1); },

    /*
     * Find the Caption object at given index
     */
    captionAtIdx: function (idx) {
        return this.track.get('clips').at(idx).caption;
    },

    playCap: function () {
        return this.captionAtIdx(this.playIdx);
    },

    editCap: function () {
        return this.editIdx() && this.captionAtIdx(this.editIdx());
    },

    /*
     * Save changes
     */
    save: function (done) {
        var self = this;
        $(self.saveButton).html('saving...').addClass('disabled');

        saveSpeakers();

        function saveSpeakers() {
            self.track.get('speakers').save({
                success: saveClips,
                error: error
            });
        }

        function saveClips () {
            self.track.get('clips').save({
                success: saveTrack,
                error: error
            });
        }

        function saveTrack () {
            self.track.save({}, {
                success: ok,
                error: error
            });
        }
        
        function ok(result) {
            $(self.saveButton).html('Save');
            self.dirty(false);
            if(done && $.isFunction(done)) done(null);
        }

        function error (err) {
            alert("Error: Unable to save.");
            $(self.saveButton).html('Save');
            self.dirty(true);
        }
    }
};

/*
 * Editor callbacks 
 * 
 * Note that all of these are bound using jQuery.proxy, so that `this`
 * refers to the correct SPINDLE.Editor object. This is not generally
 * true; for example, the Caption callbacks find their associated
 * Caption object through properties on DOM elements.
 */
SPINDLE.Editor.callbacks = {
    /* 
     * Video-player playback-head movement
     * 
     * Searches forward or backward for new transcript clip, if
     * necessary.  
     */
    update: function (ev) { 
        var playPos = this.player.currentTime,
            curClip = this.track.get('clips') && this.track.get('clips').at(this.playIdx);

        if(!curClip) return;

        if(playPos >= curClip.get('intime') &&
           playPos < curClip.get('outtime')) {
            return;
        } else if(playPos > curClip.get('outtime')
                  && this.track.get('clips').at(this.playIdx+1)
                  && playPos > this.track.get('clips').at(this.playIdx+1).get('intime')) {
            while(playPos > curClip.get('outtime')) {
                this.playIdx++;
                curClip = this.track.get('clips').at(this.playIdx);
            }
            this.justSelectedIdx = null;
        } else if(playPos < curClip.get('intime')
                  && this.playIdx > 0
                  && (this.justSelectedIdx === null || curClip.get('intime') - playPos > 1)) {
            while(playPos < curClip.get('intime')
                  && this.playIdx > 0) {
                this.playIdx--;
                curClip = this.track.get('clips').at(this.playIdx);
            }
            this.justSelectedIdx = null;
        }

        if(curClip) {
            this.redisplay();
            // Scroll the caption into view only if (1) the user
            // didn't just manually click on a caption, and (2) there
            // is no editor active.
            if(this.justSelectedIdx === null && !this.editIdx()) {
                this.scrollto();
            }
        }
    },
    
    keydown: function(ev) {
        if(ev.keyCode == SPINDLE.TAB_KEY) {
            if(ev.shiftKey) {
                ev.keyCode = SPINDLE.UP_KEY;
            } else {
                ev.keyCode = SPINDLE.DOWN_KEY;                    
            }
        }

        if(ev.keyCode == 78 && ev.ctrlKey) { ev.keyCode = 40; }
        if(ev.keyCode == 80 && ev.ctrlKey) { ev.keyCode = 38; }

        switch(ev.keyCode) {
        case SPINDLE.SPACE_KEY:
            if(ev.target.nodeName !== "INPUT" || ev.ctrlKey) {
                this.playPause();
                ev.stopPropagation();
                ev.preventDefault();
            }
            break;

        case SPINDLE.DOWN_KEY:
            this.moveDown();
            ev.preventDefault();
            ev.stopPropagation();
            break;

        case SPINDLE.UP_KEY:
            this.moveUp();
            ev.preventDefault();
            ev.stopPropagation();
            break;           
        }
    },

    addSpeaker: function () {
        var editor = SPINDLE.instance,
            newSpeakerInput = $('#new-speaker-name'),
            speakerSelector = $('#edit-speaker-select'),
            speaker = { name: newSpeakerInput.val() };
        
        editor.track.get('speakers').push(speaker);
        newSpeakerInput.val('');
        editor.updateModalDialog(speaker);
        editor.updateSpeakerSelectors();
        editor.dirty(true);
    },

    renameSpeaker: function () {
        var editor = SPINDLE.instance,
            speakerSelector = $('#edit-speaker-select'),
            speakerNameInput = $('#edit-speaker-name'),
            speaker = speakerSelector.find(':selected').data('speaker');
        
        speaker.set('name', speakerNameInput.val());
        speakerNameInput.val('');
        editor.updateModalDialog(speaker);
        editor.updateSpeakerSelectors();
        editor.dirty(true);
    },
    
    exportLink: function (ev) {
        var editor = SPINDLE.instance,
            self = this;
        
        if(editor.dirty()) {
            editor.save(function () {
                window.location = $(self).attr('href');
            });
            ev.preventDefault();            
        }
    }        
};


/*
 * Set everything up.
 */
$(function () {
    SPINDLE.instance = new SPINDLE.Editor();
    SPINDLE.instance.init();
});
