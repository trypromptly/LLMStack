import orjson as json
from rest_framework import serializers

from llmstack.jobs.models import CronJob, RepeatableJob, ScheduledJob, TaskRunLog


class TaskRunLogSerializer(serializers.ModelSerializer):
    task_uuid = serializers.SerializerMethodField()

    def get_task_uuid(self, obj):
        return obj.task_uuid()

    class Meta:
        model = TaskRunLog
        fields = ['uuid', 'task_type', 'task_uuid', 'result',
                  'status', 'errors', 'created_at']


BASE_JOB_FIELDS = [
    'uuid',
    'name',
    'task_category',
    'enabled',
    'source_uuid',
    'repeat',
    'timeout',
    'status',
    'created_at',
    'updated_at']


class BaseJobSerializer(serializers.ModelSerializer):
    source_uuid = serializers.SerializerMethodField()

    def get_source_uuid(self, obj):
        try:
            callable_args = json.loads(obj.callable_args)
            return callable_args[0]
        except BaseException:
            return None


class ScheduledJobSerializer(BaseJobSerializer):
    class Meta:
        model = ScheduledJob
        fields = BASE_JOB_FIELDS


class RepeatableJobSerializer(BaseJobSerializer):
    class Meta:
        model = RepeatableJob
        fields = BASE_JOB_FIELDS


class CronJobSerializer(BaseJobSerializer):
    class Meta:
        model = CronJob
        fields = BASE_JOB_FIELDS
