
SPINDLE.keywords = {
    init: function () {
        var keywords = $("textarea#keywords");
        $("a.tag").click(function () {
            keywords.val(keywords.val() + "," + $(this).html());
        });
    }
};


$(SPINDLE.keywords.init);