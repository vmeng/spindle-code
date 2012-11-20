$(function () {
    setInterval(SPINDLE.tasks.updateProgress, 1000);
});

SPINDLE.tasks = {
    updateProgress: function () {
        $('div.progress').each(function () {
            var that = this;
            var taskID = $(that).data('task-id');
            if(taskID) {
                var url = SPINDLE.views.task + taskID;
                $.getJSON(url, function (json) {
                    var status = json.hasOwnProperty('status') && json.status || '';
                    if(status == 'PROGRESS'
                       && json.hasOwnProperty('result')
                       && json.result) {
                        if(json.result.hasOwnProperty('progress')) {
                            var progress = json.result.progress * 100;
                            $(that).find('.bar').css('width', progress + '%');
                        }
                        
                        if(json.result.hasOwnProperty('message') && json.result.message) {
                            $(that).next('.progress-message').html(json.result.message);
                        }
                    } else if(status == 'SUCCESS') {
                        $(that).removeClass('progress-striped')
                            .data('task-id', null)
                            .find('.bar').css('width', '100%');
                        $(that).next('.progress-message').html('Finished.');
                    }
                });
            }
        });
    }
};