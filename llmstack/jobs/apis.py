import json
import logging
from datetime import datetime, timedelta

import croniter
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.apps.apis import AppViewSet
from llmstack.datasources.apis import DataSourceEntryViewSet, DataSourceViewSet
from llmstack.jobs.models import CronJob, RepeatableJob, ScheduledJob, TaskRunLog
from llmstack.jobs.serializers import TaskRunLogSerializer

logger = logging.getLogger(__name__)


class JobsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        return [IsAuthenticated()]

    def _get_job_by_uuid(self, uid, request):
        job = ScheduledJob.objects.filter(owner=request.user, uuid=uid).first()
        if not job:
            job = RepeatableJob.objects.filter(
                owner=request.user, uuid=uid).first()
        if not job:
            job = CronJob.objects.filter(owner=request.user, uuid=uid).first()
        return job

    def list(self, request):
        scheduled_jobs = ScheduledJob.objects.filter(owner=request.user)
        repeatable_jobs = RepeatableJob.objects.filter(owner=request.user)
        cron_jobs = CronJob.objects.filter(owner=request.user)
        jobs = list(map(lambda entry: entry.to_dict(), scheduled_jobs)) + list(map(
            lambda entry: entry.to_dict(), repeatable_jobs)) + list(map(lambda entry: entry.to_dict(), cron_jobs))
        return DRFResponse(status=200, data=jobs)

    def get(self, request, uid):
        job = self._get_job_by_uuid(uid, request=request)
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})
        return DRFResponse(status=200, data=job.to_dict())

    def delete(self, request, uid):
        logger.info(f"Deleting job with uuid: {uid}")
        job = self._get_job_by_uuid(uid, request=request)
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})
        # Delete all logs associated with this job
        task_logs = TaskRunLog.objects.filter(task_id=job.id)
        try:
            task_logs.delete()
        except Exception as e:
            logger.error(f"Error deleting task logs: {e}")
        job.delete()
        return DRFResponse(status=204)

    def pause(self, request, uid):
        job = self._get_job_by_uuid(uid, request=request)
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})
        job.enabled = False
        job.save()
        return DRFResponse(status=204)

    def resume(self, request, uid):
        job = self._get_job_by_uuid(uid, request=request)
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})
        job.enabled = True
        job.save()
        return DRFResponse(status=204)

    def get_tasks(self, request, uid):
        job = self._get_job_by_uuid(uid, request=request)
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})

        tasks = TaskRunLog.objects.filter(task_id=job.id).order_by('-id')
        serializer = TaskRunLogSerializer(tasks, many=True)
        return DRFResponse(status=200, data=serializer.data)


class AppRunJobsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        return [IsAuthenticated()]

    def _create_job_name(self, app_name, user, schedule_type, timestamp):
        return f"{app_name}_{user}_{schedule_type}_{timestamp}"

    def create(self, request):
        data = request.data
        app_uuid = data.get('app_uuid')
        app_detail = AppViewSet().get(request=request, uid=app_uuid).data

        app_name = app_detail.get('name')
        app_id = app_detail.get('uuid')
        frequency = data.get('frequency')
        frequency_type = frequency.get('type')

        if frequency_type not in ['run_once', 'repeat', 'cron']:
            return DRFResponse(status=400, data={'message': f"Unknown frequency type: {frequency.get('type')}"})

        scheduled_time = None
        if frequency_type == 'run_once' or frequency_type == 'repeat':
            if not frequency.get('start_date') or not frequency.get('start_time') or not frequency.get('scheduled_time'):
                return DRFResponse(status=400, data={'message': f"run_once and repeat frequency requires a start_date and start_time"})
            if frequency.get('scheduled_time'):
                scheduled_time = datetime.fromisoformat(
                    frequency.get('scheduled_time'))
            else:
                scheduled_time = timezone.make_aware(datetime.strptime(
                    f"{frequency.get('start_date')}T{frequency.get('start_time')}", "%Y-%m-%dT%H:%M:%S"), timezone.get_current_timezone())

        job_args = {
            'name': data.get('job_name',
                             self._create_job_name(app_name, request.user, frequency.get('type'), datetime.now())),
            'callable': 'llmstack.jobs.jobs.run_app',
            'callable_args': json.dumps([app_id, data['app_run_data']]),
            'callable_kwargs': json.dumps({}),
            'enabled': True,
            'queue': 'default',
            'result_ttl': 86400,
            'owner': request.user,
            'scheduled_time': scheduled_time,
            'task_category': 'app_run',
        }

        if frequency_type == 'run_once':
            job = ScheduledJob(**job_args)
            job.save()

        elif frequency_type == 'repeat':
            try:
                interval = int(frequency.get('interval', 0))
                if not interval:
                    return DRFResponse(status=400, data={'message': f"repeat frequency requires an interval greater than 0"})
            except:
                return DRFResponse(status=400, data={'message': f"repeat frequency requires an interval greater than 0"})

            job = RepeatableJob(interval=interval,
                                interval_unit='days', **job_args)
            job.save()

        elif frequency_type == 'cron':
            cron_expression = frequency.get('cron_expression')
            if not cron_expression:
                return DRFResponse(status=400, data={'message': f"cron frequency requires a cron_expression"})
            # Validate if cron expression is valid
            if not croniter.croniter.is_valid(cron_expression):
                return DRFResponse(status=400, data={'message': f"cron expression is not valid"})

            job = CronJob(cron_string=cron_expression, **job_args)
            job.save()

        return DRFResponse(status=204)


class DataSourceRefreshJobsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        return [IsAuthenticated()]

    def create(self, request):
        data = request.data
        datasource_entries = data.get('datasource_entries')
        if not datasource_entries or not isinstance(datasource_entries, list) or len(datasource_entries) == 0:
            return DRFResponse(status=400, data={'message': f"datasource_entries is empty"})

        job_name = request.data.get('job_name')
        if not job_name:
            return DRFResponse(status=400, data={'message': f"job_name is required"})

        entries = DataSourceEntryViewSet().multiGet(
            request=request, uids=datasource_entries).data
        if len(entries) != len(datasource_entries):
            return DRFResponse(status=400, data={'message': f"Invalid datasource_entries"})

        datasources = list(map(lambda entry: entry.get('datasource'), entries))
        # make sure request user has access to the datasource

        for source in datasources:
            if DataSourceViewSet().get(request=request, uid=source['uuid']).status_code != 200:
                return DRFResponse(status=400, data={'message': f"Invalid datasource_entries"})

        frequency = data.get('frequency')
        frequency_type = frequency.get('type')
        if frequency_type not in ['run_once', 'repeat', 'cron']:
            return DRFResponse(status=400, data={'message': f"Unknown frequency type: {frequency.get('type')}"})

        scheduled_time = None
        if frequency_type == 'run_once' or frequency_type == 'repeat':
            if not frequency.get('start_date') or not frequency.get('start_time') or not frequency.get('scheduled_time'):
                return DRFResponse(status=400, data={'message': f"run_once and repeat frequency requires a start_date and start_time"})
            if frequency.get('scheduled_time'):
                scheduled_time = frequency.get('scheduled_time')
            else:
                scheduled_time = timezone.make_aware(datetime.strptime(
                    f"{frequency.get('start_date')}T{frequency.get('start_time')}", "%Y-%m-%dT%H:%M:%S"), timezone.get_current_timezone())

        job_args = {
            'name': job_name,
            'callable': 'llmstack.jobs.jobs.refresh_datasource',
            'callable_args': json.dumps(datasource_entries),
            'callable_kwargs': json.dumps({}),
            'enabled': True,
            'queue': 'default',
            'result_ttl': 86400,
            'owner': request.user,
            'scheduled_time': scheduled_time,
            'task_category': 'datasource_refresh',
        }

        if frequency_type == 'run_once':
            job = ScheduledJob(**job_args)
            job.save()

        elif frequency_type == 'repeat':
            try:
                interval = int(frequency.get('interval', 0))
                if not interval:
                    return DRFResponse(status=400, data={'message': f"repeat frequency requires an interval greater than 0"})
            except:
                return DRFResponse(status=400, data={'message': f"repeat frequency requires an interval greater than 0"})

            job = RepeatableJob(interval=interval,
                                interval_unit='days', **job_args)
            job.save()

        elif frequency_type == 'cron':
            cron_expression = frequency.get('cron_expression')
            if not cron_expression:
                return DRFResponse(status=400, data={'message': f"cron frequency requires a cron_expression"})
            # Validate if cron expression is valid
            if not croniter.croniter.is_valid(cron_expression):
                return DRFResponse(status=400, data={'message': f"cron expression is not valid"})

            job = CronJob(cron_string=cron_expression, **job_args)
            job.save()

        return DRFResponse(status=204)
