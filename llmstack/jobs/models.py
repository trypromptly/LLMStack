from __future__ import unicode_literals
import importlib
from datetime import timedelta

import croniter

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.tz import utc

import django_rq

class BaseTask(models.Model):
    RQ_QUEUE_NAMES = [(key, key) for key in settings.RQ_QUEUES.keys()]
    TASK_STATUSES = [
        ('queued', 'queued'),
        ('started', 'started'),
        ('finished', 'finished'),
        ('failed', 'failed'),
        ('deferred', 'deferred'),
    ]
    
    name = models.CharField(max_length=512, unique=True)
    callable = models.CharField(max_length=2048)
    enabled = models.BooleanField(default=True)
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

    def clean(self):
        self.clean_callable()
        self.clean_queue()

    def clean_callable(self):
        try:
            self.callable_func()
        except:
            raise ValidationError({
                'callable': ValidationError(
                    _('Invalid callable, must be importable'), code='invalid')
            })

    def clean_queue(self):
        queue_keys = settings.RQ_QUEUES.keys()
        if self.queue not in queue_keys:
            raise ValidationError({
                'queue': ValidationError(
                    _('Invalid queue, must be one of: {}'.format(
                        ', '.join(queue_keys))), code='invalid')
            })

    def is_scheduled(self):
        return self.job_id and self.job_id in self.scheduler()

    def save(self, **kwargs):
        self.unschedule()
        if self.enabled:
            self.schedule()
        super(BaseTask, self).save(**kwargs)

    def delete(self, **kwargs):
        self.unschedule()
        super(BaseTask, self).delete(**kwargs)

    def scheduler(self):
        return django_rq.get_scheduler(self.queue)

    def is_schedulable(self):
        if self.job_id:
            return False
        return self.enabled

    def schedule(self):
        if self.is_schedulable() is False:
            return False
        kwargs = {}
        if self.timeout:
            kwargs['timeout'] = self.timeout
        if self.result_ttl is not None:
            kwargs['result_ttl'] = self.result_ttl
        job = self.scheduler().enqueue_at(
            self.schedule_time_utc(), self.callable_func(),
            **kwargs
        )
        self.job_id = job.id
        return True

    def unschedule(self):
        if self.is_scheduled():
            self.scheduler().cancel(self.job_id)
        self.job_id = None
        return True

    def schedule_time_utc(self):
        return utc(self.scheduled_time)

    class Meta:
        abstract = True


class ScheduledTimeMixin(models.Model):

    scheduled_time = models.DateTimeField()

    def schedule_time_utc(self):
        return utc(self.scheduled_time)

    class Meta:
        abstract = True


class ScheduledJob(ScheduledTimeMixin, BaseTask):

    class Meta:
        verbose_name = 'Scheduled Job'
        verbose_name_plural = 'Scheduled Jobs'
        ordering = ('name', )


class RepeatableJob(ScheduledTimeMixin, BaseTask):

    UNITS = [
        ('minutes', 'minutes'),
        ('hours', 'hours'),
        ('days', 'days'),
        ('weeks', 'weeks'),
    ]

    interval = models.PositiveIntegerField()
    interval_unit = models.CharField(max_length=12, choices=UNITS, default='hours')
    repeat = models.PositiveIntegerField(blank=True, null=True)

    def interval_display(self):
        return '{} {}'.format(self.interval, self.get_interval_unit_display())

    def interval_seconds(self):
        kwargs = {
            self.interval_unit: self.interval,
        }
        return timedelta(**kwargs).total_seconds()

    def schedule(self):
        if self.is_schedulable() is False:
            return False
        kwargs = {
            'scheduled_time': self.schedule_time_utc(),
            'func': self.callable_func(),
            'interval': self.interval_seconds(),
            'repeat': self.repeat
        }
        if self.timeout:
            kwargs['timeout'] = self.timeout
        if self.result_ttl is not None:
            kwargs['result_ttl'] = self.result_ttl
        job = self.scheduler().schedule(**kwargs)
        self.job_id = job.id
        return True

    class Meta:
        verbose_name = 'Repeatable Job'
        verbose_name_plural = 'Repeatable Jobs'
        ordering = ('name', )


class CronJob(BaseTask):
    result_ttl = None

    cron_string = models.CharField(max_length=64, help_text='Define the schedule in a crontab like syntax.')
    repeat = models.PositiveIntegerField(blank=True, null=True)

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

    def schedule(self):
        if self.is_schedulable() is False:
            return False
        kwargs = {
            'func': self.callable_func(),
            'cron_string': self.cron_string,
            'repeat': self.repeat
        }
        if self.timeout:
            kwargs['timeout'] = self.timeout
        job = self.scheduler().cron(**kwargs)
        self.job_id = job.id
        return True

    class Meta:
        verbose_name = 'Cron Job'
        verbose_name_plural = 'Cron Jobs'
        ordering = ('name', )