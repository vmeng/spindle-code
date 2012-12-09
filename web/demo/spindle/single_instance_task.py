from django.core.cache import cache

from celery import Task, task, current_task

class SingleInstanceTask(Task):
    """A long-running Celery task which should only execute one instance at a time."""   
    abstract = True
    django_cache_id = None
    logger = None

    def apply_async(self, *args, **kwargs):
        self.logger.debug("** apply_async called args=%s, kwargs=%s **", args, kwargs)
        def make_new_instance():
            task_instance = super(SingleInstanceTask, self).apply_async(*args, **kwargs)
            cache.set(self.django_cache_id, task_instance.task_id, 10 * 60)
            return task_instance

        # Try to grab the lock first
        if cache.add(self.django_cache_id, True, 10 * 60):
            return make_new_instance()
        else:
            task_id = cache.get(self.django_cache_id)
            # FIXME: It's possible for a previous invocation of this
            # task to die after setting the lock to True but before
            # registering its task ID. In this case it's OK to start a
            # new task.  It's also possible for the cache ID to be
            # explicitly set to None -- when?  Possibly when tasks
            # are run eagerly instead of through the queue?
            if (not task_id) or (task_id is True):
                return make_new_instance()
            else:
                task_instance = self.AsyncResult(task_id)
                self.logger.info('Task %s already running as %s', self.name, task_id)
                return task_instance
        
    def get_running_instance(self):
        task_id = cache.get(self.django_cache_id)
        if task_id and (task_id != True):
            return self.AsyncResult(task_id)
        else:
            return None

    def after_return(self, *args, **kwargs):
        cache.delete(self.django_cache_id)

    def update_progress(self, progress, message):
        # Prevent the cache key expiring
        cache.set(self.django_cache_id, self.request.id, 10 * 60)
        
        self.logger.info(u'%5.1f%% %s', 100 * progress, message)
        if not self.request.called_directly:
            self.update_state(state='PROGRESS', meta={ 'progress': progress,
                                                       'message': message })



def single_instance_task(cache_id=None, logger=None, *args, **kwargs):
    """Decorator to create single instance tasks from procedures"""
    if not cache_id:
        raise Exception("No cache_id provided to single_instance_task decorator")
    if not logger:
        raise Exception("No logger provided to single_instance_task decorator")

    def decorator(proc):
        def decorated_proc(*args, **kwargs):
            cache.set(cache_id, current_task.request.id, 60 * 60)
            return proc(*args, **kwargs)

        decorated_task = task(base=SingleInstanceTask, *args, **kwargs)(decorated_proc)
        decorated_task.django_cache_id = cache_id
        decorated_task.logger = logger
        return decorated_task

    return decorator
