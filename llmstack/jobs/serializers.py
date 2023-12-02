from rest_framework import serializers

from llmstack.jobs.models import TaskRunLog


class TaskRunLogSerializer(serializers.ModelSerializer):
    task_uuid = serializers.SerializerMethodField()

    def get_task_uuid(self, obj):
        return obj.task_uuid()

    class Meta:
        model = TaskRunLog
        fields = ['uuid', 'task_type', 'task_uuid', 'result',
                  'status', 'errors', 'created_at']
