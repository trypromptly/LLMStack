import datetime
import logging
import time
import uuid
from typing import Any, Optional

import django_rq
from django.conf import settings
from django.test import RequestFactory
from pydantic import BaseModel

from llmstack.apps.apis import AppViewSet
from llmstack.apps.models import App
from llmstack.datasources.apis import DataSourceEntryViewSet
from llmstack.datasources.models import DataSource
from llmstack.jobs.models import AdhocJob, TaskRunLog, TaskStatus

logger = logging.getLogger(__name__)


class SubTaskResult(BaseModel):
    status: TaskStatus = TaskStatus.NOT_STARTED
    output: Optional[Any] = None
    error: Optional[Any] = None


def run_app_subtask(app_id, input_data, session_id=None):
    app = App.objects.get(uuid=app_id)
    request_input_data = {"input": input_data, "stream": False}
    request = RequestFactory().post(
        f"/api/apps/{app_id}/run",
        data=request_input_data,
        format="json",
    )
    request.user = app.owner
    request.data = request_input_data
    response = AppViewSet().run(request=request, uid=app_id, session_id=session_id)
    return {
        "status_code": response.status_code,
        "data": response.data,
    }


def run_batched_app_tasks(input_data, batch_start_index, job, batch_size, task_run_log_uuid, session_id):
    for index in range(1, batch_size):
        input_data_idx = batch_start_index + index

        if not input_data_idx < len(input_data):
            break

        app_run_result = run_app_subtask(job.meta["app_id"], input_data[input_data_idx], session_id=session_id)

        if task_run_log_uuid:
            task_run_log = TaskRunLog.objects.get(uuid=uuid.UUID(task_run_log_uuid))

            if app_run_result["status_code"] == 200:
                task_run_log.result[input_data_idx] = SubTaskResult(
                    status=TaskStatus.SUCCESS, output=app_run_result["data"]
                ).dict()
            else:
                task_run_log.result[input_data_idx] = SubTaskResult(
                    status=TaskStatus.FAILURE, error=app_run_result
                ).dict()

            task_run_log.save()

        time.sleep(2)


def post_run_app_task(task_run_log_uuid, input_index, status, response, job):
    if task_run_log_uuid:
        task_run_log = TaskRunLog.objects.get(
            uuid=uuid.UUID(task_run_log_uuid),
        )
        if status == TaskStatus.SUCCESS and response["status_code"] == 200:
            task_run_log.result[input_index] = SubTaskResult(
                status=TaskStatus.SUCCESS,
                output=response["data"],
            ).dict()
        else:
            task_run_log.result[input_index] = SubTaskResult(
                status=TaskStatus.FAILURE,
                error=response,
            ).dict()

        task_run_log.save()

    # If there are more input data to process, schedule the next task
    input_data = job.meta["input_data"]
    batch_size = job.meta.get("batch_size", 1)

    if batch_size > 1 and input_index % batch_size == 0:
        session_id = None
        if job.meta.get("use_session", False):
            if "data" in response and "session" in response["data"]:
                session_id = response["data"]["session"]["id"]

        run_batched_app_tasks(input_data, input_index, job, batch_size, task_run_log_uuid, session_id)

    # If we have any more tasks to run, schedule the next task
    if input_index + batch_size < len(input_data):
        time_remaining_to_schedule_next_task = max(
            (settings.TASK_RUN_DELAY - (job.ended_at - job.started_at).total_seconds()),
            1,
        )
        logger.debug(
            f"Scheduling next task in {time_remaining_to_schedule_next_task} seconds",
        )

        django_rq.get_queue(job.meta["queue_name"]).enqueue_in(
            datetime.timedelta(seconds=5),
            run_app_subtask,
            args=(job.meta["app_id"], input_data[input_index + batch_size]),
            on_success=run_app_sub_task_success_callback,
            on_failure=run_app_sub_task_failure_callback,
            meta={
                "app_id": job.meta["app_id"],
                "task_run_log_uuid": task_run_log_uuid,
                "input_data": input_data,
                "input_data_index": input_index + batch_size,
                "queue_name": job.meta["queue_name"],
                "timeout": job.meta["timeout"],
                "result_ttl": job.meta["result_ttl"],
                "use_session": job.meta.get("use_session", False),
                "batch_size": job.meta.get("batch_size", 1),
            },
            timeout=job.meta["timeout"],
            result_ttl=job.meta["result_ttl"],
        )


def run_app_sub_task_failure_callback(job, connection, type, value, traceback):
    logger.error(
        f'task_run_log_uuid: {job.meta["task_run_log_uuid"]}, type: {type}, value: {value}, Traceback: {traceback} ',
    )
    post_run_app_task(
        job.meta["task_run_log_uuid"],
        job.meta["input_data_index"],
        TaskStatus.FAILURE,
        f"Exception: {type}, detail: {value}",
        job,
    )


def run_app_sub_task_success_callback(
    job,
    connection,
    result,
    *args,
    **kwargs,
):
    post_run_app_task(
        job.meta["task_run_log_uuid"],
        job.meta["input_data_index"],
        TaskStatus.SUCCESS,
        result,
        job,
    )


def run_app_task(app_id=None, input_data=None, *args, **kwargs):
    job_metadata = kwargs["_job_metadata"]

    timeout = 120
    result_ttl = 86400

    django_rq.get_queue("default").enqueue(
        run_app_subtask,
        args=(app_id, input_data[0]),
        on_success=run_app_sub_task_success_callback,
        on_failure=run_app_sub_task_failure_callback,
        meta={
            "app_id": app_id,
            "task_run_log_uuid": job_metadata["task_run_log_uuid"],
            "input_data": input_data,
            "input_data_index": 0,
            "queue_name": "default",
            "timeout": timeout,
            "result_ttl": result_ttl,
            "use_session": kwargs.get("use_session", False),
            "batch_size": kwargs.get("batch_size", 1),
        },
        timeout=timeout,
        result_ttl=result_ttl,
    )

    return [SubTaskResult().dict()] * len(input_data)


def upsert_datasource_entry_subtask(datasource_id, input_data):
    request_input_data = {
        "datasource_id": datasource_id,
        "input_data": input_data,
    }
    datasource = DataSource.objects.get(uuid=uuid.UUID(datasource_id))
    request = RequestFactory().post(
        "/api/datasource_entries/upsert",
        data=request_input_data,
        format="json",
    )
    request.user = datasource.owner
    request.data = request_input_data
    response = DataSourceEntryViewSet().upsert(request)

    return {
        "status_code": response.status_code,
        "data": response.data,
    }


def post_upsert_datasource_task(
    task_run_log_uuid,
    input_index,
    status,
    response,
    job,
):
    if task_run_log_uuid:
        task_run_log = TaskRunLog.objects.get(
            uuid=uuid.UUID(task_run_log_uuid),
        )
        if status == TaskStatus.SUCCESS and response["status_code"] == 200:
            task_run_log.result[input_index] = SubTaskResult(
                status=TaskStatus.SUCCESS,
                output="success",
            ).dict()
        else:
            task_run_log.result[input_index] = SubTaskResult(
                status=TaskStatus.FAILURE,
                error=response,
            ).dict()
        task_run_log.save()

    # If there are more input data to process, schedule the next task
    input_data = job.meta["input_data"]
    if input_index + 1 < len(input_data):
        time_elapsed = (job.ended_at - job.started_at).total_seconds()
        time_remaining_to_schedule_next_task = max(
            (settings.TASK_RUN_DELAY - time_elapsed),
            1,
        )
        logger.info(
            f"Scheduling next task in {time_remaining_to_schedule_next_task} seconds",
        )

        django_rq.get_queue(job.meta["queue_name"]).enqueue(
            upsert_datasource_entry_subtask,
            args=(job.meta["datasource_id"], input_data[input_index + 1]),
            on_success=upsert_datasource_entry_subtask_success_callback,
            on_failure=upsert_datasource_entry_subtask_failure_callback,
            meta={
                "datasource_id": job.meta["datasource_id"],
                "task_run_log_uuid": task_run_log_uuid,
                "task_job_uuid": job.meta.get("task_job_uuid", None),
                "input_data": input_data,
                "input_data_index": input_index + 1,
                "queue_name": job.meta["queue_name"],
                "timeout": job.meta["timeout"],
                "result_ttl": job.meta["result_ttl"],
            },
            timeout=job.meta["timeout"],
            result_ttl=job.meta["result_ttl"],
        )
    else:
        # All tasks are completed. Update the task status to completed
        task_job_uuid = job.meta.get("task_job_uuid", None)
        if task_job_uuid:
            job = AdhocJob.objects.get(uuid=uuid.UUID(task_job_uuid))
            if job:
                job.status = "finished"
                job.save()


def upsert_datasource_entry_subtask_success_callback(
    job,
    connection,
    result,
    *args,
    **kwargs,
):
    post_upsert_datasource_task(
        job.meta["task_run_log_uuid"],
        job.meta["input_data_index"],
        TaskStatus.SUCCESS,
        result,
        job,
    )


def upsert_datasource_entry_subtask_failure_callback(
    job,
    connection,
    type,
    value,
    traceback,
):
    logger.error(
        f'task_run_log_uuid: {job.meta["task_run_log_uuid"]}, type: {type}, value: {value}, Traceback: {traceback} ',
    )
    post_upsert_datasource_task(
        job.meta["task_run_log_uuid"],
        job.meta["input_data_index"],
        TaskStatus.FAILURE,
        f"Exception: {type}, detail: {value}",
        job,
    )


def upsert_datasource_entries_task(datasource_id, input_data, *args, **kwargs):
    job_metadata = kwargs["_job_metadata"]

    timeout = 120
    result_ttl = 86400

    django_rq.get_queue("default").enqueue(
        upsert_datasource_entry_subtask,
        args=(datasource_id, input_data[0]),
        on_success=upsert_datasource_entry_subtask_success_callback,
        on_failure=upsert_datasource_entry_subtask_failure_callback,
        meta={
            "datasource_id": datasource_id,
            "task_run_log_uuid": job_metadata.get("task_run_log_uuid", None),
            "task_job_uuid": job_metadata.get("task_job_uuid", None),
            "input_data": input_data,
            "input_data_index": 0,
            "queue_name": "default",
            "timeout": timeout,
            "result_ttl": result_ttl,
        },
        timeout=timeout,
        result_ttl=result_ttl,
    )

    return [SubTaskResult().dict()] * len(input_data)
