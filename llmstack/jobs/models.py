# A lot of the implementation is adopted from django-rq and django-tasks-scheduler
from __future__ import unicode_literals
import importlib
from datetime import timedelta
import logging
import math
import uuid 
import croniter
import json

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.tz import utc
from django.utils import timezone
from django.contrib.auth.models import User

import django_rq
from rq import Queue, get_current_job

logger = logging.getLogger(__name__)

SCHEDULER_INTERVAL = 60

class TaskRunLog(models.Model):
    TASK_TYPES = [
        ('ScheduledJob', 'ScheduledJob'),
        ('RepeatableJob', 'RepeatableJob'),
        ('CronJob', 'CronJob'),
    ]
    STATUS = [
        ('started', 'started'),
        ('running', 'running'),
        ('succeeded', 'succeeded'),
        ('failed', 'failed'),
        ('stopped', 'stopped'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    task_id = models.CharField(max_length=128, editable=False, null=False)
    task_type = models.CharField(max_length=128, choices=TASK_TYPES, editable=False, null=False)
    job_id = models.CharField(max_length=128, editable=False, blank=True, null=False)
    result = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, null = False)
    errors = models.JSONField(blank=True, null=True)
    ends_at = models.DateTimeField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def _get_ends_at(self):
        raise NotImplementedError
        
    def task_name(self):
        entry = apps.get_model(app_label='jobs', model_name=self.task_type).objects.filter(id=self.task_id).first()
        return entry.name if entry else ''
        
    
    def user(self):
        entry = apps.get_model(app_label='jobs', model_name=self.task_type).objects.filter(id=self.task_id).first()
        return entry.owner if entry else ''
    
    def __str__(self) -> str:
        return self.job_id
    
    class Meta:
        ordering = ('-created_at', )
        

def get_scheduled_task(task_model: str, task_id: int):
    if not task_model:
        return None
    
    model = apps.get_model(app_label='jobs', model_name=task_model)
    task = model.objects.filter(id=task_id).first()
    if task is None:
        raise ValueError(f'Job {task_model}:{task_id} does not exit')
    return task

def failure_callback(job, connection, type, value, traceback):
    task = get_scheduled_task(job.meta.get('task_type', None), job.meta.get('scheduled_task_id'))
    if task is None:
        return 
    
    task_log = TaskRunLog.objects.filter(job_id=job.id, task_id=task.id).first()
    if task_log is None:
        logger.error(f'Could not find task log for job {job.id}')
    else:
        task_log.status = 'failed'
        task_log.errors = {
            'type': type,
            'value': value,
            'traceback': traceback,
        }
        task_log.save()
    
    task.job_id = None
    task.save(schedule_job=True)
    
def success_callback(job, connection, result, *args, **kwargs):
    task = get_scheduled_task(job.meta.get('task_type', None), job.meta.get('scheduled_task_id'))
    if task is None:
        return 
    
    task_log = TaskRunLog.objects.filter(job_id=job.id, task_id=task.id).first()
    if task_log is None:
        logger.error(f'Could not find task log for job {job.id}')
    else:
        task_log.status = 'succeeded'
        task_log.result = {'result': result}
        task_log.save()
    
    task.job_id = None
    # If task is a scehduledJob we have already ran the job no need to schedule it again
    task.save(schedule_job= False if task.TASK_TYPE == 'ScheduledJob' else True) 
    
def stopped_callback(job, connection):
    task = get_scheduled_task(job.meta.get('task_type', None), job.meta.get('scheduled_task_id'))
    if task is None:
        return
    
    task_log = TaskRunLog.objects.filter(job_id=job.id, task_id=task.id).first()
    if task_log is None:
        logger.error(f'Could not find task log for job {job.id}')
    else:
        task_log.status = 'stopped'
        task_log.save()
    
    task.job_id = None
    task.save(chedule_job= False if task.TASK_TYPE == 'ScheduledJob' else True)

def run_task(task_model: str, task_id: int):
    job = get_current_job()
    task_run_log = TaskRunLog.objects.create(
        task_id=task_id,
        task_type=task_model,
        job_id=job.id,
        status='started',
    )
    task = get_scheduled_task(task_model, task_id)
    
    if task is None:
        logger.error(f'Could not find task {task_model}:{task_id}')
        return False
    
    if timezone.now() > task.end_time and task.TASK_TYPE == 'ScheduledJob':
        # Task got scheduled post the end time
         results = {}
         errors = {'detail': 'Task got scheduled post the end time'}
    else:    
        args = task.parse_args()
        kwargs = task.parse_kwargs()
        results, errors = task.callable_func()(*args, **kwargs)
    
    task_run_log.result = results
    task_run_log.errors = errors
    task_run_log.save()
    
    return True

class BaseTask(models.Model):
    TASK_TYPE = 'BaseTask'
    
    RQ_QUEUE_NAMES = [(key, key) for key in settings.RQ_QUEUES.keys()]
    TASK_STATUSES = [
        ('queued', 'queued'),
        ('started', 'started'),
        ('finished', 'finished'),
        ('failed', 'failed'),
        ('deferred', 'deferred'),
    ]
    TASK_CATEGORY = [
        ('generic', 'generic'),
        ('app_run', 'app_run'),
        ('data_refresh', 'data_refresh'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=512, unique=True)
    callable = models.CharField(max_length=2048)
    callable_args = models.TextField(blank=True, null=True)
    callable_kwargs = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    repeat = models.PositiveIntegerField(blank=True, null=True, help_text=
                                         'Number of times to repeat the job. Blank repeats forever.')
    queue = models.CharField(choices=RQ_QUEUE_NAMES, max_length=32)
    job_id = models.CharField(max_length=128, editable=False, blank=True, null=True)
    timeout = models.IntegerField(blank=True, null=True, help_text=
                                  'Timeout specifies the maximum runtime, in seconds, for the job '
                                  'before it\'ll be considered \'lost\'. Blank uses the default timeout.'
    )
    status = models.CharField(max_length=50, null=False, choices=TASK_STATUSES, default='queued')
    result_ttl = models.IntegerField( blank=True, null=True,
                                     help_text='The TTL value (in seconds) of the job result. -1: '
                                     'Result never expires, you should delete jobs manually. '
                                     '0: Result gets deleted immediately. >0: Result expires '
                                     'after n seconds.')
    owner = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, help_text='Owner of the task', null=False
    )
    task_category = models.CharField(max_length=128, choices=TASK_CATEGORY, editable=False, null=False, default='generic') 
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def callable_func(self):
        path = self.callable.split('.')
        module = importlib.import_module('.'.join(path[:-1]))
        func = getattr(module, path[-1])
        if callable(func) is False:
            raise TypeError("'{}' is not callable".format(self.callable))
        return func
    
    def parse_args(self):
        args = {}
        try:
            args = json.loads(self.callable_args) if self.callable_args else {}
        except:
            pass
        return args
    
    def parse_kwargs(self):
        kwargs = {}
        try:
            kwargs = json.loads(self.callable_kwargs) if self.callable_kwargs else {}
        except:
            pass
        return kwargs
    
    def is_scheduled(self):
        if self.job_id is None:
            return False
        scheduled_jobs = self.schedule_job_registry().get_job_ids()
        enqueued_jobs = self.rqueue.get_job_ids()
        active_jobs = self.active_job_registry().get_job_ids()
        res = ((self.job_id in scheduled_jobs)
               or (self.job_id in enqueued_jobs)
               or (self.job_id in active_jobs))
        # If the job_id is not scheduled/enqueued/started,
        # update the job_id to None. (The job_id belongs to a previous run which is completed)
        if not res:
            self.job_id = None
            super(BaseTask, self).save()
        return res

    def function_string(self):
        args = self.callable_args or ''
        kwargs = self.callable_kwargs or ''
        return '{}({}, {})'.format(self.callable, args, kwargs)
        
    def _next_job_id(self):
        return f"{str(uuid.uuid4())}"
    
    def _get_job_meta(self):
        return dict(
                repeat=self.repeat,
                task_type=self.TASK_TYPE,
                scheduled_task_id=self.id)
        
    
    @property
    def rqueue(self) -> Queue:
        return django_rq.get_queue(self.queue)
    
    def can_be_scheduled(self):
        """
        Is the task ready to be scheduled?
        If the task is already scheduled or disabled, then it is not
        ready to be scheduled.
        """
        if self.is_scheduled() or not self.enabled:
            logger.debug('Task is already scheduled or disabled: {}'.format(self))
            return False
        return True
    
    def schedule(self):
        """ 
        Schedule the next execution for the task.
        """
        if not self.can_be_scheduled():
            return False
        
        schedule_time = self._schedule_time()
        job = self.rqueue.enqueue_at(schedule_time, 
                                     run_task, 
                                     args=(self.TASK_TYPE, self.id),
                                     on_success=success_callback,
                                     on_failure=failure_callback,
                                     job_id=self._next_job_id(),
                                     meta=self._get_job_meta(),
                                     job_timeout=self.timeout,
                                     result_ttl=self.result_ttl,
                                     )
        self.job_id = job.id
        super(BaseTask, self).save()
        return True
    
    def enqueue_to_run(self) -> bool:
        """Enqueue job to run now."""
        kwargs = self._enqueue_args()
        job = self.rqueue.enqueue(
            run_task,
            args=(self.TASK_TYPE, self.id),
            **kwargs,
        )
        self.job_id = job.id
        self.save(schedule_job=False)
        return True
    
    def unschedule(self):
        """ 
        Remove a job from the queue.
        """
        if self.job_id is None:
            return 
        self.rqueue.remove(self.job_id)
        self.schedule_job_registry().remove(self.job_id)
        self.job_id = None
        self.save(schedule_job = False)
        return True
    
    def _schedule_time(self):
        return utc(self.scheduled_time) if settings.USE_TZ else self.scheduled_time       
    
    def to_dict(self):
        res = dict(
            uuid=self.uuid,
            model=self.TASK_TYPE,
            task_category=self.task_category,
            name=self.name,
            callable=self.callable,
            callable_args=self.callable_args,
            callable_kwargs=self.callable_kwargs,
            enabled=self.enabled,
            queue=self.queue,
            repeat=self.repeat,
            timeout=self.timeout,
            result_ttl=self.result_ttl,
            cron_string=getattr(self, 'cron_string', None),
            scheduled_time=self._schedule_time().isoformat(),
            interval=getattr(self, 'interval', None),
            interval_unit=getattr(self, 'interval_unit', None),
        )
        return res
    
    def __str__(self):
        return f'{self.TASK_TYPE}:{self.name}:func={self.callable}'
    
    def save(self, **kwargs):
        schedule_job = kwargs.pop('schedule_job', True)
        update_fields = kwargs.get('update_fields', None)
        if update_fields:
            kwargs['update_fields'] = set(update_fields).union({'updated_at'})
        super(BaseTask, self).save(**kwargs)
        if schedule_job:
            self.schedule()
            super(BaseTask, self).save()
    
    def delete(self, **kwargs):
        self.unschedule()
        super(BaseTask, self).delete(**kwargs)
        
    def _clean_callable(self):
        try:
            self.callable_func()
        except:
            logger.error('Invalid callable: {}'.format(self.callable))
            raise ValidationError({
                'callable': ValidationError('Invalid callable, must be importable', code='invalid')
            })
    
    def _clean_queue(self):
        queue_keys = settings.RQ_QUEUES.keys()
        if self.queue not in queue_keys:
            raise ValidationError({
                'queue': ValidationError(
                    'Invalid queue, must be one of: {}'.format(', '.join(queue_keys)), code='invalid')
            })
    def clean(self):
        self._clean_callable()
        self._clean_queue()

    def schedule_job_registry(self):
        from rq.registry import ScheduledJobRegistry
        return ScheduledJobRegistry(queue=self.rqueue)
    
    def active_job_registry(self):
        from rq.registry import StartedJobRegistry
        return StartedJobRegistry(queue=self.rqueue)

    def schedule_time_utc(self):
        return utc(self.scheduled_time)

    class Meta:
        abstract = True


class ScheduledTimeMixin(models.Model):
    scheduled_time = models.DateTimeField()

    class Meta:
        abstract = True


class ScheduledJob(ScheduledTimeMixin, BaseTask):
    TASK_TYPE = 'ScheduledJob'
    repeat = None
    
    def can_be_scheduled(self):
        return super(ScheduledJob, self).can_be_scheduled() and (
            self.scheduled_time is None
                     or self.scheduled_time >= timezone.now())

    class Meta:
        verbose_name = 'Scheduled Job'
        verbose_name_plural = 'Scheduled Jobs'
        ordering = ('name', )


class RepeatableJob(ScheduledTimeMixin, BaseTask):
    TASK_TYPE = 'RepeatableJob'

    UNITS = [
        ('minutes', 'minutes'),
        ('hours', 'hours'),
        ('days', 'days'),
        ('weeks', 'weeks'),
    ]

    interval = models.PositiveIntegerField()
    interval_unit = models.CharField(max_length=12, choices=UNITS, default='hours')

    def interval_display(self):
        return '{} {}'.format(self.interval, self.get_interval_unit_display())

    def interval_seconds(self):
        kwargs = {
            self.interval_unit: self.interval,
        }
        return timedelta(**kwargs).total_seconds()
    
    def clean(self):
        super(RepeatableJob, self).clean()
        self.clean_interval_unit()
        self.clean_result_ttl()
        
    def clean_interval_unit(self):
        if SCHEDULER_INTERVAL > self.interval_seconds():
            raise ValidationError(
                "Job interval is set lower than %(queue)r queue's interval. "
                  "minimum interval is %(interval)",
                code='invalid',
                params={'queue': self.queue, 'interval': SCHEDULER_INTERVAL})
        if self.interval_seconds() % SCHEDULER_INTERVAL:
            raise ValidationError(
                "Job interval is not a multiple of rq_scheduler's interval frequency: %(interval)ss",
                code='invalid',
                params={'interval': SCHEDULER_INTERVAL})
    
    def clean_result_ttl(self) -> None:
        """
        Throws an error if there are repeats left to run and the result_ttl won't last until the next scheduled time.
        :return: None
        """
        if self.result_ttl and self.result_ttl != -1 and self.result_ttl < self.interval_seconds() and self.repeat:
            raise ValidationError(
                "Job result_ttl must be either indefinite (-1) or "
                  "longer than the interval, %(interval)s seconds, to ensure rescheduling.",
                code='invalid',
                params={'interval': self.interval_seconds()}, )
    
    def _get_job_meta(self):
        res = super(RepeatableJob, self)._get_job_meta()
        res['interval'] = self.interval_seconds()
        return res
    
    def _schedule_time(self):
        _now = timezone.now()
        if self.scheduled_time >= _now:
            return super(RepeatableJob, self)._schedule_time()
        
        gap = math.ceil((_now - self.scheduled_time).total_seconds() / self.interval_seconds())
        if self.repeat is None or self.repeat >= gap:
            self.scheduled_time += timedelta(seconds=self.interval_seconds() * gap)
            self.repeat = (self.repeat - gap) if self.repeat is not None else None
        return super(RepeatableJob, self)._schedule_time()
    
    def can_be_scheduled(self):
        if super(RepeatableJob, self).can_be_scheduled() is False:
            return False
        if self._schedule_time() < timezone.now():
            return False
        return True
            
    class Meta:
        verbose_name = 'Repeatable Job'
        verbose_name_plural = 'Repeatable Jobs'
        ordering = ('name', )


def get_next_cron_time(cron_string) -> timezone.datetime:
    """Calculate the next scheduled time by creating a crontab object
    with a cron string"""
    now = timezone.now()
    itr = croniter.croniter(cron_string, now)
    next_itr = itr.get_next(timezone.datetime)
    return next_itr

class CronJob(BaseTask):
    TASK_TYPE = 'CronJob'

    cron_string = models.CharField(max_length=64, help_text='Define the schedule in a crontab like syntax.')

    def clean(self):
        super(CronJob, self).clean()
        self.clean_cron_string()

    def clean_cron_string(self):
        try:
            croniter.croniter(self.cron_string)
        except ValueError as e:
            raise ValidationError({
                'cron_string': ValidationError(
                    str(e), code='invalid')
            })

    def _schedule_time(self):
        self.scheduled_time = get_next_cron_time(self.cron_string)
        return super()._schedule_time()

    class Meta:
        verbose_name = 'Cron Job'
        verbose_name_plural = 'Cron Jobs'
        ordering = ('name', )