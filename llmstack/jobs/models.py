from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict
import uuid
from django.conf import settings

from django.contrib.auth.models import User
from django.db import models
from django.contrib import admin
from django.forms import ValidationError
import django_rq
from queue import Queue


QUEUE_CHOICES = ((key, key) for key in settings.RQ_QUEUES.keys())
TASK_STATUS_CHOICES = (
    ('queued', 'Queued'),
    ('started', 'Started'),
    ('finished', 'Finished'),
    ('failed', 'Failed'),
)

logger = logging.getLogger(__name__)

class BaseTask(models.Model):
    TASK_TYPE = 'BaseTask'
    name = models.CharField(max_length=255)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue = models.CharField(max_length=255, choices=QUEUE_CHOICES)
    enabled = models.BooleanField(default=False, help_text='Enable this task to be run.')
    repeat = models.PositiveIntegerField(blank=True, null=True,
        help_text='Number of times to run the job. Leaving this blank means it will run forever.')
    job_id = models.CharField(max_length=255, blank=True, null=True, editable=False)
    timeout = models.IntegerField(blank=True, null=True, help_text='Timeout in seconds.')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    @admin.display(boolean=True, description=_('is scheduled?'))
    def is_scheduled(self) -> bool:
        if self.job_id is None:  # no job_id => is not scheduled
            return False
        scheduled_jobs = self.rqueue.scheduled_job_registry.get_job_ids()
        enqueued_jobs = self.rqueue.get_job_ids()
        active_jobs = self.rqueue.started_job_registry.get_job_ids()
        res = ((self.job_id in scheduled_jobs)
               or (self.job_id in enqueued_jobs)
               or (self.job_id in active_jobs))
        # If the job_id is not scheduled/enqueued/started,
        # update the job_id to None. (The job_id belongs to a previous run which is completed)
        if not res:
            self.job_id = None
            super(BaseTask, self).save()
        return res
    
    
    def _next_job_id(self):
        addition = uuid.uuid4().hex[-10:]
        name = self.name.replace('/', '.')
        return f'{self.queue}:{name}:{addition}'
    
    @property
    def job_queue(self):
        if self._use_redis:
            return django_rq.queues.get_queue(self.queue_name)
        else:
            return Queue()
        
    def ready_for_schedule(self) -> bool:
        """Is the task ready to be scheduled?

        If the task is already scheduled or disabled, then it is not
        ready to be scheduled.

        :returns: True if the task is ready to be scheduled.
        """
        if self.is_scheduled():
            logger.debug(f'Task {self.name} already scheduled')
            return False
        if not self.enabled:
            logger.debug(f'Task {str(self)} disabled, enable task before scheduling')
            return False
        return True
    
    def add_to_queue(self, *args, **kwargs):
        if self._use_redis:
            queue = django_rq.get_queue(self.queue_name)
            return queue.enqueue_job(job=self)
        else:
            with ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(self.func, *self.args, **self.kwargs)
            
    
    def schedule(self) -> bool:
        """Schedule the next execution for the task to run.
        :returns: True if a job was scheduled, False otherwise.
        """
        if not self.ready_for_schedule():
            return False
        schedule_time = self._schedule_time()
        job = self.rqueue.enqueue_at(
            schedule_time,
            tools.run_task,
            args=(self.TASK_TYPE, self.id),
            **kwargs, )
        self.job_id = job.id
        super(BaseTask, self).save()
        return True
    
    def enqueue_to_run(self) -> bool:
        """Enqueue job to run now."""
        kwargs = self._enqueue_args()
        job = self.rqueue.enqueue(
            tools.run_task,
            args=(self.TASK_TYPE, self.id),
            **kwargs,
        )
        self.job_id = job.id
        self.save(schedule_job=False)
        return True
    
    def unschedule(self) -> bool:
        """Remove a job from django-queue.

        If a job is queued to be executed or scheduled to be executed, it will remove it.
        """
        queue = self.rqueue
        if self.job_id is None:
            return True
        queue.remove(self.job_id)
        queue.scheduled_job_registry.remove(self.job_id)
        self.job_id = None
        self.save(schedule_job=False)
        return True
    
    def _schedule_time(self):
        return utc(self.scheduled_time) if django_settings.USE_TZ else self.scheduled_time

    def to_dict(self) -> Dict:
        """Export model to dictionary, so it can be saved as external file backup"""
        res = dict(
            model = self.TASK_TYPE,
            name=self.name,
            enabled=self.enabled,
            queue=self.queue,
            repeat=self.repeat,
            timeout=self.timeout,
            cron_string=getattr(self, 'cron_string', None),
            scheduled_time=self._schedule_time().isoformat(),
            interval=getattr(self, 'interval', None),
            interval_unit=getattr(self, 'interval_unit', None),
        )
        return res
    
    def __str__(self):
        return f'{self.TASK_TYPE}[{self.name}={self.job_id}]'
    
    def save(self, **kwargs):
        schedule_job = kwargs.pop('schedule_job', True)
        update_fields = kwargs.get('update_fields', None)
        if update_fields:
            kwargs['update_fields'] = set(update_fields).union({'modified'})
        super(BaseTask, self).save(**kwargs)
        if schedule_job:
            self.schedule()
            super(BaseTask, self).save()

    def delete(self, **kwargs):
        self.unschedule()
        super(BaseTask, self).delete(**kwargs)
        
    def clean_queue(self):
        queue_keys = settings.QUEUES.keys()
        if self.queue not in queue_keys:
            raise ValidationError({
                'queue': ValidationError(
                    _('Invalid queue, must be one of: {}'.format(
                        ', '.join(queue_keys))), code='invalid')
            })
    
    def clean(self):
        self.clean_queue()
        self.clean_callable()
        
    class Meta:
        abstract = True
        
class ScheduledTimeMixin(models.Model):
    scheduled_time = models.DateTimeField()

    class Meta:
        abstract = True
        
class ScheduledAppRunTask(ScheduledTimeMixin, BaseTask):
    repeat = None
    TASK_TYPE = 'ScheduledAppRunTask'
    
    def ready_for_schedule(self) -> bool:
        return (super(ScheduledAppRunTask, self).ready_for_schedule()
                and (self.scheduled_time is None
                     or self.scheduled_time >= timezone.now()))
    
    class Meta:
        verbose_name = 'Scheduled AppRun Task'
        verbose_name_plural = 'Scheduled AppRun Tasks'
        ordering = ('name',)

class RepeatableAppRunTask(ScheduledTimeMixin, BaseTask):
    class TimeUnits(models.TextChoices):
        SECONDS = 'seconds', 'seconds'
        MINUTES = 'minutes', 'minutes'
        HOURS = 'hours', 'hours'
        DAYS = 'days', 'days'
        WEEKS = 'weeks', 'weeks'
    
    interval = models.PositiveIntegerField()
    interval_unit = models.CharField(
        max_length=12, choices=TimeUnits.choices, default=TimeUnits.HOURS
    )
    TASK_TYPE = 'RepeatableAppRunTask'
    
    def clean(self):
        super(RepeatableAppRunTask, self).clean()
        self.clean_interval_unit()

    def clean_interval_unit(self):
        if SCHEDULER_INTERVAL > self.interval_seconds():
            raise ValidationError(
                _("Job interval is set lower than %(queue)r queue's interval. "
                  "minimum interval is %(interval)"),
                code='invalid',
                params={'queue': self.queue, 'interval': SCHEDULER_INTERVAL})
        if self.interval_seconds() % SCHEDULER_INTERVAL:
            raise ValidationError(
                _("Job interval is not a multiple of rq_scheduler's interval frequency: %(interval)ss"),
                code='invalid',
                params={'interval': SCHEDULER_INTERVAL})
            
    def interval_display(self):
        return '{} {}'.format(self.interval, self.get_interval_unit_display())
    
    def interval_seconds(self):
        kwargs = {self.interval_unit: self.interval, }
        return timedelta(**kwargs).total_seconds()
    
    
    def _schedule_time(self):
        _now = timezone.now()
        if self.scheduled_time >= _now:
            return super()._schedule_time()
        gap = math.ceil((_now.timestamp() - self.scheduled_time.timestamp()) / self.interval_seconds())
        if self.repeat is None or self.repeat >= gap:
            self.scheduled_time += timedelta(seconds=self.interval_seconds() * gap)
            self.repeat = (self.repeat - gap) if self.repeat is not None else None
        return super()._schedule_time()
    
    def ready_for_schedule(self):
        if super(RepeatableTask, self).ready_for_schedule() is False:
            return False
        if self._schedule_time() < timezone.now():
            return False
        return True
    
    class Meta:
        verbose_name = 'Repeatable AppRun Task'
        verbose_name_plural = 'Repeatable AppRun Tasks'
        ordering = ('name',)
    
    
class CronAppRunTask(BaseTask):
    TASK_TYPE = 'CronAppRunTask'
    
    cron_string = models.CharField(max_length=255)
    
    def clean(self):
        super(CronAppRunTask, self).clean()
        self.clean_cron_string()
        
    def clean_cron_string(self):
        try:
            croniter.croniter(self.cron_string)
        except ValueError as e:
            raise ValidationError({'cron_string': ValidationError(_(str(e)), code='invalid')})
    
    def _schedule_time(self):
        self.scheduled_time = tools.get_next_cron_time(self.cron_string)
        return super()._schedule_time()
    
    class Meta:
        verbose_name = 'Cron AppRun Task'
        verbose_name_plural = 'Cron AppRun Tasks'
        ordering = ('name',)
    