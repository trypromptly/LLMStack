import logging
import uuid
from rq import get_current_job

from llmstack.datasources.models import DataSource
from llmstack.datasources.types import DataSourceTypeFactory
from llmstack.jobs.models import AdhocJob, TaskRunLog

logger = logging.getLogger(__name__)


def process_datasource_add_entry_request(datasource_id, input_data, job_id, **kwargs):
    from llmstack.jobs.jobs import upsert_datasource_entries_task

    job = get_current_job()
    adhoc_job = AdhocJob.objects.get(uuid=uuid.UUID(job_id))

    adhoc_job.job_id = job.id
    adhoc_job.status = 'started'
    adhoc_job.save()

    datasource = DataSource.objects.get(uuid=uuid.UUID(datasource_id))
    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource.type)
    datasource_entry_handler = datasource_entry_handler_cls(datasource)

    datasource_entry_items = datasource_entry_handler.validate_and_process(
        input_data)
    datasource_entry_items = list(
        map(lambda x: x.dict(), datasource_entry_items))

    task_run_log = TaskRunLog(
        task_type=adhoc_job.TASK_TYPE,
        task_id=adhoc_job.id,
        job_id=job.id,
        status='started',
    )
    task_run_log.save()

    kwargs = {
        '_job_metadata': {
            'task_run_log_uuid': str(task_run_log.uuid),
            'task_job_uuid': job_id
        },
    }

    results = upsert_datasource_entries_task(
        datasource_id, datasource_entry_items, **kwargs)

    task_run_log.result = results
    task_run_log.save()

    return task_run_log.uuid
