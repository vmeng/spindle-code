$(function () {
    setInterval(SPINDLE.queue.updateProgress, 5000);
});

SPINDLE.queue = {};
SPINDLE.queue.updateProgress = function () {
    $.get(SPINDLE.views.queuepartial, function (html) {
        var table = $(html).filter('#queue-table');
        if(table.length) {
            $('#queue-table').replaceWith(table);
        };
    });
};