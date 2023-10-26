import logging
import croniter 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.contrib.auth.models import User

from llmstack.apps.apis import AppViewSet
from llmstack.jobs.models import ScheduledJob, RepeatableJob, CronJob

logger = logging.getLogger(__name__)

def run_app(app_id, input_data):
    logger.info(f"run_app app_id: {app_id}, input_data: {input_data}")
    return True

class JobsViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        if self.action == 'submit_job':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def _create_job_name(self, app_name, user, schedule_type, timestamp):
        return f"{app_name}_{user}_{schedule_type}_{timestamp}"
    
    @csrf_exempt
    def app_run_submit(self, request):
        data = request.data
        app_uuid = data.get('app_uuid')
        app_detail = AppViewSet().get(request=request, uid=app_uuid).data
        
        app_name = app_detail.get('name')
        app_id = app_detail.get('uuid')
        
        frequency = data.get('frequency')
        
        if frequency.get('type') not in ['run_once', 'repeat', 'cron']:
            raise Exception(f"Unknown frequency type: {frequency.get('type')}")
        
        job_name = self._create_job_name(app_name, request.user, frequency.get('type'), datetime.now())
        
        if frequency.get('type') == 'run_once':
            scheduled_time = datetime.strptime(f"{frequency.get('start_date')}T{frequency.get('start_time')}", "%Y-%m-%dT%H:%M:%S")
            if not scheduled_time:
                raise Exception(f"run_once frequency requires a scheduled_time")
            
            job = ScheduledJob(
                name=job_name,
                callable=run_app,
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
            logger.info(f"run_once app_id: {app_id}, job: {job}") 
        elif frequency.get('type') == 'repeat':
            scheduled_time = datetime.strptime(f"{frequency.get('start_date')}T{frequency.get('start_time')}", "%Y-%m-%dT%H:%M:%S")
            interval = frequency.get('interval')
            if not scheduled_time:
                raise Exception(f"repeat frequency requires a scheduled_time")
            job = RepeatableJob(
                name=job_name,
                callable=run_app,
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
            logger.info(f"repeat app_id: {app_id}, job: {job}")
            
        elif frequency.get('type') == 'cron':
            cron_expression = frequency.get('cron_expression')
            if not cron_expression:
                raise Exception(f"cron frequency requires a cron_expression")
            # Validate if cron expression is valid
            if not croniter.croniter.is_valid(cron_expression):
                raise Exception(f"cron expression is not valid")
            
            job = CronJob(
                name=job_name,
                callable=run_app,
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
    