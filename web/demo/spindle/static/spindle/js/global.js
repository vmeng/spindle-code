
/*
 * Global namespace object
 */
var SPINDLE = {
    
    /* Some constants for keys */
    BACKSPACE_KEY: 8,
    TAB_KEY: 9,    

    RETURN_KEY : 13,

    LEFT_KEY: 37, 
    UP_KEY : 38,
    RIGHT_KEY: 39,
    DOWN_KEY : 40,
    
    SPACE_KEY : 32,
    FULL_STOP_KEY: 190,

    /*
     * Generic AJAX communication functions
     */
    get: function(url, data, succ, fail) {
        $.ajax({ type: 'get',
                 url: url,                 
                 data: data,
                 success: this.ajaxSuccess(succ, fail),
                 error: this.ajaxError(succ, fail)});
    },

    post: function(url, data, succ, fail) {
        $.ajax({ type: 'post',
                 url: url,
                 contentType: 'application/json',
                 data: JSON.stringify(data),
                 success: this.ajaxSuccess(succ, fail),
                 error: this.ajaxError(succ, fail)});
    },

    ajaxSuccess: function(succ, fail) {
        return function(r) {
            if(r.status === "ok") {
                if(typeof succ === 'function') { succ(r); }
            } else {
                if(typeof fail === 'function') { fail(r); }
            }
        };
    },

    ajaxError: function(succ, fail) {
        return function (xhr, msg, err) {
            if(typeof fail === 'function') { fail(err); }
        };
    }   
};
