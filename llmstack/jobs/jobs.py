import datetime
import uuid
from llmstack.apps.models import App
from django.test import RequestFactory
from django.conf import settings

from llmstack.apps.apis import AppViewSet
import django_rq
import logging

from llmstack.jobs.models import TaskRunLog 

logger = logging.getLogger(__name__)

SUCCESS = 'success'
FAILURE = 'failure'

def run_app_subtask(app_id, input_data):
    app = App.objects.get(uuid=app_id)
    request_input_data = {'input' : input_data, 'stream': False}
    request = RequestFactory().post(f'/api/apps/{app_id}/run', data=request_input_data, format='json')
    request.user = app.owner
    request.data = request_input_data
    response = AppViewSet().run(request=request, uid=app_id)
    return {
        'status_code': response.status_code,
        'data': response.data
    }

def post_run_app_task(task_run_log_uuid, input_index, status, response, job):
    task_run_log = TaskRunLog.objects.get(uuid=uuid.UUID(task_run_log_uuid))
    if status == SUCCESS and response['status_code'] == 200:
        task_run_log.result[input_index] = response['data']
    else:
        task_run_log.errors[input_index] = {'detail': str(response)}
    task_run_log.save()
    
    # If there are more input data to process, schedule the next task
    input_data = job.meta['input_data']
    if input_index + 1 < len(input_data):
        time_elapsed = (job.ended_at - job.started_at).total_seconds()
        time_remaining_to_schedule_next_task = max((settings.TASK_RUN_DELAY - time_elapsed), 1)
        logger.info(f'Scheduling next task in {time_remaining_to_schedule_next_task} seconds')
        
        django_rq.get_queue(job.meta['queue_name']).enqueue_in(
            datetime.timedelta(seconds=time_remaining_to_schedule_next_task),
            run_app_subtask,
            args=(job.meta['app_id'], input_data[input_index + 1]),
            on_success=run_app_sub_task_success_callback,
            on_failure=run_app_sub_task_failure_callback,
            meta={
                'app_id': job.meta['app_id'],
                'task_run_log_uuid': task_run_log_uuid,
                'input_data': input_data,
                'input_data_index': input_index + 1,
                'queue_name': job.meta['queue_name'],
                'timeout': job.meta['timeout'],
                'result_ttl': job.meta['result_ttl'],
                },
            timeout=job.meta['timeout'],
            result_ttl=job.meta['result_ttl']
        )
        
def run_app_sub_task_failure_callback(job, connection, type, value, traceback):
    logger.error(f'task_run_log_uuid: {job.meta["task_run_log_uuid"]}, type: {type}, value: {value}, Traceback: {traceback} ')
    post_run_app_task(job.meta['task_run_log_uuid'], job.meta['input_data_index'],
                      FAILURE, f'Exception: {type}, detail: {value}', job)
    
def run_app_sub_task_success_callback(job, connection, result, *args, **kwargs):
    post_run_app_task(job.meta['task_run_log_uuid'], job.meta['input_data_index'],
                      SUCCESS, result, job)

def run_app_task(app_id=None, input_data=None, *args, **kwargs):
    job_metadata = kwargs['_job_metadata']
    
    timeout =  120
    result_ttl =  86400
    
    django_rq.get_queue('default').enqueue(
        run_app_subtask,
        args=(app_id, input_data[0]),
        on_success=run_app_sub_task_success_callback,
        on_failure=run_app_sub_task_failure_callback,
        meta={
            'app_id': app_id,
            'task_run_log_uuid': job_metadata['task_run_log_uuid'],
            'input_data': input_data,
            'input_data_index': 0,
            'queue_name': 'default',
            'timeout': timeout,
            'result_ttl': result_ttl,
            },
        timeout=timeout,
        result_ttl=result_ttl)
    
    return [None] * len(input_data), [None] * len(input_data)

def refresh_datasource(datasource_entries=[], *args, **kwargs):
    from llmstack.datasources.apis import DataSourceViewSet
    
    return None, None