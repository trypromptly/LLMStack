import logging
import croniter 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from datetime import datetime, timedelta
from django.utils import timezone

from llmstack.apps.apis import AppViewSet
from llmstack.jobs.models import ScheduledJob, RepeatableJob, CronJob, AppRunJobLog
from rq import get_current_job

logger = logging.getLogger(__name__)

def run_app(app_id, input_data):
    job = get_current_job()
    logger.info(f"run_app app_id: {app_id}, input_data: {input_data}")
    for entry in input_data:
        logger.info(f"run_app entry: {entry}")
        
    app_run_request_id = 'test'
    AppRunJobLog.objects.create(
        task_id=job.args[1],
        task_type=job.args[0],
        job_id=job.id,
        app_run_request_id=app_run_request_id,
    )
    
    return True

class AppRunJobsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        return [IsAuthenticated()]
    
    def _create_job_name(self, app_name, user, schedule_type, timestamp):
        return f"{app_name}_{user}_{schedule_type}_{timestamp}"
    
    def post(self, request):
        data = request.data
        app_uuid = data.get('app_uuid')
        app_detail = AppViewSet().get(request=request, uid=app_uuid).data
        
        app_name = app_detail.get('name')
        app_id = app_detail.get('uuid')        
        frequency = data.get('frequency')
        
        job_name = data.get('job_name', self._create_job_name(app_name, request.user, frequency.get('type'), datetime.now()))

        
        if frequency.get('type') not in ['run_once', 'repeat', 'cron']:
            return DRFResponse(status=400, data={'message': f"Unknown frequency type: {frequency.get('type')}"})
                
        if frequency.get('type') == 'run_once':
            scheduled_time = timezone.make_aware(datetime.strptime(f"{frequency.get('start_date')}T{frequency.get('start_time')}", "%Y-%m-%dT%H:%M:%S"), timezone.get_current_timezone())
            if not scheduled_time:
                return DRFResponse(status=400, data={'message': f"run_once frequency requires a scheduled_time"})
            
            job = ScheduledJob(
                name=job_name,
                callable='llmstack.jobs.apis.run_app',
                callable_kwargs={
                    'app_id': app_id,
                    'input_data': data
                },
                enabled=True,
                queue='default',
                result_ttl=-1,
                owner=request.user,
                scheduled_time=scheduled_time,
            )
            job.save()
            
        elif frequency.get('type') == 'repeat':
            scheduled_time = timezone.make_aware(datetime.strptime(f"{frequency.get('start_date')}T{frequency.get('start_time')}", "%Y-%m-%dT%H:%M:%S"), timezone.get_current_timezone())
            try:
                interval = int(frequency.get('interval', 0))
                if not interval:
                    return DRFResponse(status=400, data={'message': f"repeat frequency requires an interval greater than 0"})
            except:
                return DRFResponse(status=400, data={'message': f"repeat frequency requires an interval greater than 0"})
                
            if not scheduled_time:
                return DRFResponse(status=400, data={'message': f"repeat frequency requires a scheduled_time"})
            
            job = RepeatableJob(
                name=job_name,
                callable='llmstack.jobs.apis.run_app',
                callable_kwargs={
                    'app_id': app_id,
                    'input_data': data
                },
                enabled=True,
                queue='default',
                result_ttl=-1,
                owner=request.user,
                scheduled_time=scheduled_time,
                interval=interval,
                interval_unit='days'
            )
            job.save()
            
        elif frequency.get('type') == 'cron':
            cron_expression = frequency.get('cron_expression')
            if not cron_expression:
                return DRFResponse(status=400, data={'message': f"cron frequency requires a cron_expression"})
            # Validate if cron expression is valid
            if not croniter.croniter.is_valid(cron_expression):
                return DRFResponse(status=400, data={'message': f"cron expression is not valid"})
            
            job = CronJob(
                name=job_name,
                callable='llmstack.jobs.apis.run_app',
                callable_kwargs={
                    'app_id': app_id,
                    'input_data': data
                },
                enabled=True,
                queue='default',
                result_ttl=-1,
                owner=request.user,
                cron_string=cron_expression
            )
            logger.info(f"cron app_id: {app_id}, job: {job}")
        
        return DRFResponse(status=204)
    
    def list(self, request):
        scheduled_jobs = ScheduledJob.objects.filter(owner=request.user)
        repeatable_jobs = RepeatableJob.objects.filter(owner=request.user)
        cron_jobs = CronJob.objects.filter(owner=request.user)
        jobs = list(map(lambda entry: entry.to_dict(),scheduled_jobs)) + list(map(lambda entry: entry.to_dict(),repeatable_jobs)) + list(map(lambda entry: entry.to_dict(),cron_jobs))
        return DRFResponse(status=200, data=jobs)
    
    def get(self, request, uid):
        job = ScheduledJob.objects.get(owner=request.user, uuid=uid)
        if not job:
            job = RepeatableJob.objects.get(owner=request.user, uuid=uid)
        
        if not job:
            job = CronJob.objects.get(owner=request.user, uuid=uid)
            
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})

        return DRFResponse(status=200, data=job.to_dict())
    
    def delete(self, request, uid):
        job = ScheduledJob.objects.get(owner=request.user, uuid=uid)
        if not job:
            job = RepeatableJob.objects.get(owner=request.user, uuid=uid)
        
        if not job:
            job = CronJob.objects.get(owner=request.user, uuid=uid)
            
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})

        job.delete()
        return DRFResponse(status=204)
    
    def pause(self, request, uid):
        # Check if it exists in ScheduledJob table
        job = ScheduledJob.objects.get(owner=request.user, uuid=uid)
        if not job:
            job = RepeatableJob.objects.get(owner=request.user, uuid=uid)
        
        if not job:
            job = CronJob.objects.get(owner=request.user, uuid=uid)
            
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})
        
        job.enabled = False
        job.save()
        return DRFResponse(status=204)
    
    def resume(self, request, uid):
        # Check if it exists in ScheduledJob table
        job = ScheduledJob.objects.get(owner=request.user, uuid=uid)
        if not job:
            job = RepeatableJob.objects.get(owner=request.user, uuid=uid)
        
        if not job:
            job = CronJob.objects.get(owner=request.user, uuid=uid)
            
        if not job:
            return DRFResponse(status=404, data={'message': f"No job found with uuid: {uid}"})
        
        job.enabled = True
        job.save()
        return DRFResponse(status=204)
    