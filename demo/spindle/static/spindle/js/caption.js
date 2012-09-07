/* -*- js2-additional-externs: ("SPINDLE" "sprintf") -*- */

/* 
 * class Caption
 *
 * View class for one editable "clip", or line of caption text, on the
 * screen
 *
 */
SPINDLE.Caption = 
    function (owner, clip, active, isSpeakerChange) {
        this.owner = owner;
        this.clip = clip;
        this.clip.caption = this;
        this.active = active;
        this.isSpeakerChange = isSpeakerChange;
        this.makeElements();
    };
    
/*
 * Class methods
 */

/* Find an Caption object from a DOM element */
SPINDLE.Caption.fromDOM = function (elem) {
    var $elem = $(elem);
    
    if(! $elem.is(".caption")) {
        $elem = $elem.parents(".caption");
    }
    
    if(!$elem.length) {
        return null;
    }
    return $elem.data("caption");
};

/* Utility: format a time nicely */
SPINDLE.Caption.formatTime = function (secs) {
    var minutes, hours;
    
    if(secs < 60) {
        return sprintf("%2ds", secs);
    }

    minutes = Math.floor(secs/60);
    secs = secs - 60*minutes;
    if(minutes < 60) {
        return sprintf("%2dm%2ds", minutes, secs);
    }

    hours = Math.floor(minutes/60);
    minutes = minutes - 60*hours;

    return sprintf("%2dh%2dm%2ds", hours, minutes, secs);
};

/*
 * Instance methods
 */
SPINDLE.Caption.prototype = {
    /* SPINDLE.Editor object this belongs to */
    owner: undefined,

    /* Properties */
    clip: undefined,
    active: false,
    isSpeakerChange: false,

    /* References to DOM elements */
    dom: undefined,             // enclosing tag
    input: undefined,           // text box
    timecode: undefined,        // timecode
    para: undefined,            // "begin paragraph" toggle
    speakerSelect: undefined,         // "select speaker" popup

    /* 
     * Create the DOM elements 
     */
    makeElements: function () {
        var Caption = SPINDLE.Caption, clip = this.clip,
            outer = $("#caption-view-template")
                .clone()
                .removeAttr('id')
                .data("caption", this),

            timecode = outer.find(".timecode")
                .html(Caption.formatTime(clip.get('intime')))
                .bind("click", Caption.callbacks.dblclick),

            para = outer.find(".paragraph-toggle")
                .addClass(this.clip.get('begin_para') ? 'active' : '')
                .click(Caption.callbacks.toggleBeginPara),

            speaker = outer.find(".speaker-selector"),            

            input = outer.find(".caption-text")
                .attr("value", clip.get('caption_text'))
                .bind("keydown", Caption.callbacks.keydown)
                .keypress(Caption.callbacks.keypress)
                .bind("focus", Caption.callbacks.focus)
                .change(Caption.callbacks.changeText); 

        this.makeSpeakerSelector(speaker);

        if(!this.clip.get('edited')) outer.addClass('unedited');
        if(this.active) outer.addClass('active');

        if(this.dom) {
            $(this.dom).replaceWith(outer);
        }

        this.dom = outer[0];
        this.input = input[0];
        this.timecode = timecode[0];
        this.para = para[0];
        this.speakerSelect = speaker[0];
    },
        
    /*
     * Generate speaker-selector popups
     */

    // Re-generate the speaker menu, after speakers are edited
    updateSpeakerSelector: function () {
        var newSelector = this.makeSpeakerSelector();
        $(this.speakerSelect).replaceWith(newSelector);
        this.speakerSelect = newSelector.get(0);
    },
    
    // Generate the DOM element
    makeSpeakerSelector: function (elem) {
        var self = this,
            select, option,
            Caption = SPINDLE.Caption;
        
        if(elem === undefined) {
            select = $("<select />")
                .addClass("speaker-selector");
        } else {
            select = elem;
        }

        select.bind("change", Caption.callbacks.changeSpeaker);
        if(this.isSpeakerChange) select.addClass("speaker-change");

        option = $("<option />")
            .html("(no speaker)")
            .attr('disabled', 'disabled');
        if(! self.clip.get('speaker')) option.attr('selected', 'selected');
        select.append(option);

        if(this.owner.track.get('speakers').length) {
            this.owner.track.get('speakers').each(function(speaker, idx) {
                option = $("<option />")
                    .html(speaker.get('name') + ": ")
                    .data("speaker", speaker);

                if(speaker === self.clip.get('speaker'))
                    option.attr('selected', 'selected');

                select.append(option);
            });
        } else {
            option = $("<option />");
            select.append(option);
        }
        
        option = $("<option />")
            .html("Edit speakers...")
            .attr('value', "edit-speakers");
        select.append(option);
        
        return select;
    },

    /*
     *  Update the DOM to reflect current values of this.clip
     */
    redisplay: function () {
        var widget = $(this.dom);
        if(this.active) {
            widget.addClass("active");
        } else {
            widget.removeClass("active");
        }

        if(this.clip.get('edited')) {
            widget.removeClass('unedited');
        } else {
            widget.addClass('unedited');
        }
    },

    /* Make active or inactive
     *
     * The active clip is the one which corresponds to the current
     * play position of the audio/video player.
     */
    makeActive: function(active) {
        if(active === undefined) active = true;

        this.active = active;
        this.redisplay();
    },
    
    /* Make focused */
    focus: function () {
        this.input.focus();
    },

    /* Accessors/Setters */
    edited: function (setTo) {
        if(setTo === undefined) return this.clip.get('edited');

        var wasEdited = this.clip.get('edited');
        this.clip.set('edited', setTo);

        if(this.clip.get('edited') !== wasEdited) {
            this.redisplay();
            if(this.clip.get('edited')) {
                this.owner.editedCount++;
                this.owner.updateStats();
            }
        }

        if(this.clip.get('edited')) this.owner.dirty(true); 
    },

    text: function (setTo) {
        if(setTo === undefined) return $(this.input).val();
        
        var oldText = this.clip.get('caption_text');
        this.clip.set('caption_text', setTo);        
        $(this.input).val(setTo);
        
        if(oldText !== this.clip.get('caption_text')) this.edited(true);
        this.redisplay();

        return setTo;
    },

    begin_para: function (setTo) {
        if(setTo === undefined)
            return $(this.para).hasClass('active');

        this.clip.set('begin_para', setTo);
        if(setTo) {
            $(this.para).addClass('active');
        } else {
            $(this.para).removeClass('active');
        }
    },

    speaker: function (setTo) {
        var widget = $(this.speakerSelect);        
        if(setTo === undefined)
            return widget.find("option:selected").data('speaker');

        this.clip.set('speaker', setTo);
        widget.find("option").each(function (idx, elem) {
            var $elem = $(elem);
            if($elem.data('speaker') == setTo)
                $elem.attr('selected', 'selected');
            else
                $elem.removeAttr('selected');
        });
        return setTo;
    },

    /* Position of cursor */
    point: function (setTo) {
        if(typeof setTo !== 'undefined')
            return this.input.selectionStart = this.input.selectionEnd = setTo;
        else
            return this.input.selectionStart;
    },

    selectionEmpty: function () {
        return this.input.selectionStart === this.input.selectionEnd;
    },

    delete: function () {
        var self = this;

        $(self.dom).remove();
        self.owner.removeClip(self.clip);
    },

    insertSentenceBreak: function (ch) {
        var input = this.input, point = this.point(),
            text = this.text(), newText;
        
        if(point == text.length) {
            var nextClip = this.owner.clipAfter(this.clip),
                nextText = nextClip.caption.text(),
                newNextText = nextText.replace(/^(\s*)(.)/, function(m, ws, letter) {
                    return letter.toUpperCase();
                });

            newText = text + ".";

            this.text(newText);
            nextClip.caption.text(newNextText);

            this.owner.editClip(nextClip);
            nextClip.caption.point(0);
        } else {
            var beforeText = text.substring(0, point).replace(/\s*$/, ''),
                afterText = text.substring(point).replace(/^\s*/, '');
            
            newText = beforeText + ch + " " 
                + afterText.replace(/^./, function(letter) {
                    return letter.toUpperCase();
                });
            
            this.text(newText);

            this.point(point + 1);
        }
        return false;
    },

    insertComma: function () {
        var input = this.input, text = this.text(), point = this.point(),
            beforeText = text.substring(0, point).replace(/\s*$/, ''),
            afterText = text.substring(point).replace(/^\s*/, ''),
            newText = beforeText + ', ' + afterText;
        this.text(newText);
        this.point(beforeText.length + 1);
    },

    /* Split this caption at point */
    split: function () {
        var text = this.text(), point = this.point(),

            ratio = point / text.length,
            splitTime = this.clip.get('intime')
                + ratio * (this.clip.get('outtime') - this.clip.get('intime')),
            
            newClip = new Clip({
                caption_text: text.substring(point).replace(/^\s*/, ""),
                intime: splitTime,
                outtime: this.clip.get('outtime'),
                speaker: this.clip.get('speaker'),
                begin_para: false,
                edited: true }),
            newCaption,

            self = this;
        
        // Create caption for newly inserted clip
        newCaption = new SPINDLE.Caption(self.owner, newClip);

        // Insert new caption into the page
        $(self.dom).after(newCaption.dom);

        // Insert new clip into transcript
        self.owner.insertClipAfter(newClip, self.clip);

        self.owner.editClip(newClip);
        newCaption.point(0);

        // Update this clip
        self.clip.set('outtime', splitTime);
        self.text(text.substring(0, point));
    },
    

    /* Join with prev */
    join: function () {
        var prevClip = this.owner.clipBefore(this.clip),
            self = this;

        if(!prevClip) {
            return; 
        }

        // Remove clip from transcript
        self.clip.collection.remove(self.clip);

        // Update previous clip 
        var prevText = prevClip.caption.text(),
            point = prevText.length;
        prevClip.set('outtime', self.clip.get('outtime'));
        prevText = prevText + " " + self.text();
        prevText = prevText.replace(/\s+/, ' ');

        // ... and edit the caption
        prevClip.caption.text(prevText);
        self.owner.editClip(prevClip);
        prevClip.caption.point(point); 

        // Remove ourselves from DOM      
        self.delete();      
    }
};

/*
 * SPINDLE.Caption element callbacks
 */
SPINDLE.Caption.callbacks = {        
    /* Click on the caption outside of the input element: jump the
     * editor to this point
     */
    dblclick: function () {
        var caption = SPINDLE.Caption.fromDOM(this);
        
        caption.owner.jumpToClip(caption.clip);
    },
    
    focus: function () {
        var caption = SPINDLE.Caption.fromDOM(this);

        caption.owner.editClip(caption.clip, true);
    },

    keydown: function (ev) {
        var caption = SPINDLE.Caption.fromDOM(this);

        switch(ev.keyCode) {        
            // Return: Split clip at point                    
        case SPINDLE.RETURN_KEY:
            caption.split();
            ev.stopPropagation();
            break;
            
            // Backspace: Join with previous clip
        case SPINDLE.BACKSPACE_KEY:
            ev.stopPropagation();
            if(ev.ctrlKey || (caption.point() == 0 && caption.selectionEmpty())) {
                ev.preventDefault();
                caption.join();
            }
            break;
            
            // TAB and Shift-TAB are handled by the editor's DIV
            // handler, but we need to turn off the browser's default
            // next/prev-field behavior
        case SPINDLE.TAB_KEY:
            ev.preventDefault();
            break;

            // Right and left: move to next/previous caption if point
            // is at beginning or end of this one
        case SPINDLE.RIGHT_KEY:
            if(caption.point() == caption.text().length) {
                caption.owner.moveDown();
                ev.preventDefault();
            }
            break;
            
        case SPINDLE.LEFT_KEY:
            if(caption.point() == 0) {
                caption.owner.moveUp();
                ev.preventDefault();
            }
            break;

        }
    },

    keypress: function (ev) {
        var caption = SPINDLE.Caption.fromDOM(this),
            chr = String.fromCharCode(ev.which);

        switch(chr) {
            case ".":
            case "?":
            caption.insertSentenceBreak(chr);
            ev.preventDefault();
            break; 

            case ",":
            caption.insertComma();
            ev.preventDefault();
            break;
        }        
    },

    changeText: function(ev) {
        var caption = SPINDLE.Caption.fromDOM(this);
        caption.text($(this).val());
    },

    toggleBeginPara: function(ev) {
        var caption = SPINDLE.Caption.fromDOM(this);
        $(this).button('toggle');
        caption.clip.set('begin_para', $(this).hasClass('active'));
        caption.owner.dirty(true);
    },

    changeSpeaker: function () {
        var caption = SPINDLE.Caption.fromDOM(this),
            clips = caption.owner.track.get('clips'),
            clip = caption.clip,
            oldSpeaker = clip.get('speaker'),
            newSpeaker = caption.speaker(),
            idx;

        if($(this).val() == 'edit-speakers') {
            caption.owner.editSpeakers();
            caption.speaker(oldSpeaker);
            return;
        }

        idx = clips.indexOf(clip);

        for(var i = idx;
            i < clips.length && clips.at(i).get('speaker') === oldSpeaker;
            i++) {
            clips.at(i).caption.speaker(newSpeaker);
        }

        caption.isSpeakerChange = (idx == 0)
            || caption.clip.get('speaker') !== clips.at(idx-1).get('speaker');
        caption.updateSpeakerSelector();

        caption.owner.dirty(true);
    }
        
};
