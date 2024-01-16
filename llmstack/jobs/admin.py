from django.conf import settings
from django.contrib import admin

from .models import AdhocJob, ScheduledJob, RepeatableJob, CronJob, TaskRunLog

QUEUES = [(key, key) for key in settings.RQ_QUEUES.keys()]


class QueueMixin(object):
    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(QueueMixin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def get_form(self, request, obj=None, **kwargs):
        queue_field = self.model._meta.get_field('queue')
        queue_field.choices = QUEUES
        return super(QueueMixin, self).get_form(request, obj, **kwargs)

    def delete_model(self, request, obj):
        if hasattr(obj, 'all'):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()

    delete_model.short_description = "Delete selected %(verbose_name_plural)s"


class ScheduledJobAdmin(QueueMixin, admin.ModelAdmin):
    list_display = (
        'uuid',
        'name',
        'job_id',
        'is_scheduled',
        'scheduled_time',
        'enabled',
        'function_string')
    list_filter = ('enabled', )
    list_editable = ('enabled', )
    readonly_fields = ('job_id', )
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'callable_args', 'callable_kwargs', 'enabled'),
        }),
        ('RQ Settings', {
            'fields': ('queue', 'job_id', ),
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_time',
                'timeout',
                'result_ttl'
            ),
        }),
    )


class RepeatableJobAdmin(QueueMixin, admin.ModelAdmin):
    list_display = (
        'name', 'job_id', 'is_scheduled', 'scheduled_time', 'interval_display',
        'enabled')
    list_filter = ('enabled', )
    list_editable = ('enabled', )
    readonly_fields = ('job_id', )
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'enabled', ),
        }),
        ('RQ Settings', {
            'fields': ('queue', 'job_id', ),
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_time',
                ('interval', 'interval_unit', ),
                'repeat',
                'timeout',
                'result_ttl'
            ),
        }),
    )


class CronJobAdmin(QueueMixin, admin.ModelAdmin):
    list_display = (
        'name', 'job_id', 'is_scheduled', 'cron_string', 'enabled')
    list_filter = ('enabled', )
    list_editable = ('enabled', )

    readonly_fields = ('job_id', )
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'enabled', ),
        }),
        ('RQ Settings', {
            'fields': ('queue', 'job_id', ),
        }),
        ('Scheduling', {
            'fields': (
                'cron_string',
                'repeat',
                'timeout',
            ),
        }),
    )


class AdhocJobAdmin(QueueMixin, admin.ModelAdmin):
    list_display = (
        'name', 'job_id', 'enabled')
    list_filter = ('enabled', )
    list_editable = ('enabled', )

    readonly_fields = ('job_id', 'status', 'queue', 'metadata')
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'status', 'metadata'),
        }),
        ('RQ Settings', {
            'fields': ('queue', 'job_id', ),
        }),

    )


class TaskRunLogAdmin(admin.ModelAdmin):
    list_display = (
        'task_name', 'user', 'job_id', 'status', 'created_at',
    )
    readonly_fields = ('uuid', 'task_name', 'task_type', 'user',
                       'job_id', 'result', 'errors', 'status', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('uuid', 'created_at', 'job_id')
        }),
        ('Task Info', {
            'fields': ('task_name', 'task_type', 'result', 'errors', 'status', 'user')
        })
    )


admin.site.register(ScheduledJob, ScheduledJobAdmin)
admin.site.register(RepeatableJob, RepeatableJobAdmin)
admin.site.register(CronJob, CronJobAdmin)
admin.site.register(TaskRunLog, TaskRunLogAdmin)
admin.site.register(AdhocJob, AdhocJobAdmin)
