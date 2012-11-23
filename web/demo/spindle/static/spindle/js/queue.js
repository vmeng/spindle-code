$(function () {
    setInterval(SPINDLE.queue.updateProgress, 5000);
    $('.confirmed-delete-button').live('click', function (ev) {
        $('[name=delete_task_id]').val($(this).data('task-id'));
        $('#confirm-delete-modal').modal();
        ev.preventDefault();
    });

    $('.immediate-delete-button').live('click', function ()  {
        $('[name=delete_task_id]').val($(this).data('task-id'));
        $('form').submit();
    });                                        
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