/* -*- js2-additional-externs: ("SPINDLE" "sprintf") -*- */

/*
 * class Caption
 *
 * View class for one editable "clip", or line of caption text, on the
 * screen
 *
 */
SPINDLE.Caption = Backbone.View.extend({
    initialize: function (options) {
        this.owner = options.owner;
        this.clip = options.clip;
        this.clip.caption = this;
        this.clip.on('change', this.onChange, this);

        this.active = !!options.active;
    },

    /*
     * Class methods
     */

    /* Utility: format a time nicely */
    formatTime: function (secs) {
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
    },

    /* SPINDLE.Editor object this belongs to */
    owner: undefined,

    /* Properties */
    clip: undefined,
    active: false,

    /* References to DOM elements */
    input: undefined,           // text box
    timecode: undefined,        // timecode
    para: undefined,            // "begin paragraph" toggle
    speakerSelect: undefined,         // "select speaker" popup

    events: {
        "click .timecode": "dblclick",

        "keydown .caption-text": "keydown",
        "focus .caption-text": "onFocus",
        "change .caption-text": "changeText",
        "keypress .caption-text": "keypress",

        "click .paragraph-toggle": "toggleBeginPara",

        "change .speaker-selector": "changeSpeaker"
    },

    /*
     * Create the DOM elements
     */
    render: function () {
        var clip = this.clip,
            outer = $("#caption-view-template")
                .clone()
                .removeAttr('id'),

            timecode = outer.find(".timecode")
                .html(this.formatTime(clip.get('intime'))),

            para = outer.find(".paragraph-toggle")
                .addClass(this.clip.get('begin_para') ? 'active' : ''),

            speaker = outer.find(".speaker-selector"),

            input = outer.find(".caption-text")
                .attr("value", clip.get('caption_text'));

        this.makeSpeakerSelector(speaker);

        if(!this.clip.get('edited'))
            outer.addClass('unedited');
        if(this.active)
            outer.addClass('active');

        // if(this.dom) {
        //     $(this.dom).replaceWith(outer);
        // }

        this.setElement(outer[0]);

        this.input = input[0];
        this.timecode = timecode[0];
        this.para = para[0];
        this.speakerSelect = speaker[0];

        return this;
    },

    onChange: function () {
        var self = this,
            track, speaker, speakers, clips, idx, isSpeakerChange;

        clips = this.clip.collection;
        if(!clips)              // This clip has been deleted
            return;

        idx = clips.indexOf(this.clip);

        track = clips.track;

        speaker = this.clip.get('speaker');
        speakers = track.get('speakers');
        isSpeakerChange = idx == 0
            || clips.at(idx - 1).get('speaker') !== this.clip.get('speaker');

        function setClassIf($el, cond, clss) {
            if(cond) $el.addClass(clss);
            else $el.removeClass(clss);
        }

        $(this.input).val(this.clip.get('caption_text'));

        setClassIf(this.$el, this.active, 'active');
        setClassIf(this.$el, !this.clip.get('edited'), 'unedited');
        setClassIf($(this.para), this.clip.get('begin_para'), 'active');
        setClassIf($(this.speakerSelect), isSpeakerChange, 'speaker-change');

        if(speaker) $(this.speakerSelect).val(speaker.cid);
    },

    // Re-generate the speaker menu, after speakers are edited
    onSpeakerChange: function () {
        this.makeSpeakerSelector(this.speakerSelect);
    },

    // Generate the speaker selector
    makeSpeakerSelector: function (elem) {
        var self = this,
            select, option,
            Caption = SPINDLE.Caption,
            track = this.owner.track,
            speakers = track.get('speakers'),
            clips = track.get('clips'),
            idx = clips.indexOf(this.clip);

        if(idx == -1) return;    // HACK FIXME

        var isSpeakerChange = idx == 0
                || clips.at(idx - 1).get('speaker') !== this.clip.get('speaker');

        if(elem === undefined) {
            select = $("<select />").addClass("speaker-selector");
        } else {
            select = $(elem);
            select.html('');
        }

        if(isSpeakerChange) select.addClass("speaker-change");

        option = $("<option />")
            .html("(no speaker)")
            .attr('disabled', 'disabled');
        if(! self.clip.get('speaker')) option.attr('selected', 'selected');
        select.append(option);

        if(speakers.length) {
            speakers.each(function(speaker, idx) {
                option = $("<option />")
                    .html(speaker.get('name') + ": ")
                    .attr('value', speaker.cid)
                    .data("speaker", speaker);

                if(speaker === self.clip.get('speaker'))
                    option.attr('selected', 'selected');

                select.append(option);
            });
        } else {
            option = $("<option />");
            select.append(option);
        }

        speakers.on('add change remove', this.onSpeakerChange, this);

        option = $("<option />")
            .html("Edit speakers...")
            .attr('value', "edit-speakers");
        select.append(option);

        return select;
    },

    /* Make active or inactive
     *
     * The active clip is the one which corresponds to the current
     * play position of the audio/video player.
     */
    makeActive: function(active) {
        if(active === undefined) active = true;

        this.active = active;
        this.onChange();
    },

    makeFocused: function () {
        this.input.focus();
    },

    /* Accessors/Setters */
    edited: function (setTo) {
        if(setTo === undefined) return this.clip.get('edited');

        var wasEdited = this.clip.get('edited');
        this.clip.set('edited', setTo);

        if(this.clip.get('edited') !== wasEdited) {
            if(this.clip.get('edited')) {
                this.owner.editedCount++;
                this.owner.updateStats();
            }
        }
    },

    text: function () {
        return $(this.input).val();
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

        self.$el.remove();
        self.clip.off('change');
        self.clip.collection.remove(self.clip);
        self.deleted = true;
    },

    insertSentenceBreak: function (ch) {
        var input = this.input, point = this.point(),
            text = this.text(), newText;

        if(point == text.length) {
            var nextClip = this.owner.clipAfter(this.clip),
                nextText = nextClip.get('caption_text'),
                newNextText = nextText.replace(/^(\s*)(.)/, function(m, ws, letter) {
                    return letter.toUpperCase();
                });

            newText = text + ".";

            this.clip.set('caption_text', newText);
            nextClip.set('caption_text', newNextText);

            this.owner.editClip(nextClip);
            nextClip.caption.point(0);
        } else {
            var beforeText = text.substring(0, point).replace(/\s*$/, ''),
                afterText = text.substring(point).replace(/^\s*/, '');

            newText = beforeText + ch + " "
                + afterText.replace(/^./, function(letter) {
                    return letter.toUpperCase();
                });

            this.clip.set('caption_text', newText);

            this.point(point + 1);
        }
        return false;
    },

    insertComma: function () {
        var input = this.input, text = this.text(), point = this.point(),
            beforeText = text.substring(0, point).replace(/\s*$/, ''),
            afterText = text.substring(point).replace(/^\s*/, ''),
            newText = beforeText + ', ' + afterText;
        this.clip.set('caption_text', newText);
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
                track: this.clip.get('track'),
                begin_para: false,
                edited: true }),
            newCaption,

            self = this;

        // Insert new clip into transcript
        self.clip.collection.add(newClip);

        // Create caption for newly inserted clip
        newCaption = new SPINDLE.Caption({
            owner: self.owner,
            clip: newClip
        });

        // Insert new caption into the page
        self.$el.after(newCaption.render().el);

        self.owner.editClip(newClip);
        newCaption.point(0);

        // Update this clip
        self.clip.set('outtime', splitTime);
        self.clip.set('caption_text', text.substring(0, point));
    },


    /* Join with prev */
    join: function () {
        var idx = this.clip.collection.indexOf(this.clip),
            prevClip, self = this;

        if(idx == 0)
            return;

        prevClip = this.clip.collection.at(idx - 1);

        // Update previous clip
        var prevText = prevClip.get('caption_text'),
            point = prevText.length;
        prevClip.set('outtime', self.clip.get('outtime'));
        prevText = prevText + " " + self.text();
        prevText = prevText.replace(/\s+/, ' ');
        prevClip.set('caption_text', prevText);

        // Remove ourselves from DOM
        self.delete();

        // ... and edit the caption
        self.owner.editClip(prevClip);
        prevClip.caption.point(point);
    },

    /*
     *  callbacks
     */

    /* Click on the caption outside of the input element: jump the
     * editor to this point
     */
    dblclick: function () {
        this.owner.jumpToClip(this.clip);
    },

    onFocus: function () {
        this.owner.editClip(this.clip, true);
    },

    keydown: function (ev) {
        switch(ev.keyCode) {
            // Return: Split clip at point
        case SPINDLE.RETURN_KEY:
            this.split();
            ev.stopPropagation();
            break;

            // Backspace: Join with previous clip
        case SPINDLE.BACKSPACE_KEY:
            ev.stopPropagation();
            if(ev.ctrlKey || (this.point() == 0 && this.selectionEmpty())) {
                ev.preventDefault();
                this.join();
            }
            break;

            // TAB and Shift-TAB are handled by the editor's DIV
            // handler, but we need to turn off the browser's default
            // next/prev-field behavior
        case SPINDLE.TAB_KEY:
            ev.preventDefault();
            break;

            // Right and left: move to next/previous this if point
            // is at beginning or end of this one
        case SPINDLE.RIGHT_KEY:
            if(this.point() == this.text().length) {
                this.owner.moveDown();
                ev.preventDefault();
            }
            break;

        case SPINDLE.LEFT_KEY:
            if(this.point() == 0) {
                this.owner.moveUp();
                ev.preventDefault();
            }
            break;

        }
    },

    keypress: function (ev) {
        var chr = String.fromCharCode(ev.which);

        switch(chr) {
        case ".":
        case "?":
            this.insertSentenceBreak(chr);
            ev.preventDefault();
            break;

        case ",":
            this.insertComma();
            ev.preventDefault();
            break;
        }
    },

    changeText: function(ev) {
        this.clip.set('caption_text', $(ev.target).val());
    },

    toggleBeginPara: function(ev) {
        $(ev.target).button('toggle');
        this.clip.set('begin_para', $(ev.target).hasClass('active'));
    },

    changeSpeaker: function (ev) {
        var track = this.clip.track,
            clip = this.clip,
            clips = clip.collection,
            oldSpeaker = clip.get('speaker'),
            newSpeaker = this.speaker(),
            idx;

        if($(ev.target).val() == 'edit-speakers') {
            this.owner.editSpeakers();
            this.clip.trigger('change');
            return;
        }

        idx = clips.indexOf(clip);

        for(var i = idx;
            i < clips.length && clips.at(i).get('speaker') === oldSpeaker;
            i++) {
            clips.at(i).set('speaker', newSpeaker);
        }
    }

});
