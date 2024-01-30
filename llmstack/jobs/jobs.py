import datetime
import logging
import uuid
from typing import Any, List, Optional

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


class TaskRunner:
    @staticmethod
    def run_subtask(*args, **kwargs) -> List[SubTaskResult]:
        raise NotImplementedError

    @staticmethod
    def schedule_next_batch(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_input_data_batch(input_data, input_data_index, batch_size):
        return input_data[input_data_index : input_data_index + batch_size]

    @staticmethod
    def update_task_run_log_results(task_run_log_uuid, start_index, results):
        task_run_log = TaskRunLog.objects.get(uuid=uuid.UUID(task_run_log_uuid))
        for idx in range(len(results)):
            logger.info(f"Type: {type(results[idx])}, Result: {results[idx]}")
            task_run_log.result[start_index + idx] = results[idx]
        task_run_log.save()


class TaskRunJobMeta(BaseModel):
    task_run_type: str
    task_run_log_uuid: str
    input_data: List[Any]
    input_data_index: int
    batch_size: int
    queue_name: str
    result_ttl: int


class AppRunTaskRunner(TaskRunner):
    class JobMetadata(TaskRunJobMeta):
        app_id: str
        use_session: bool

    class SubTaskArgs(BaseModel):
        app_id: str
        use_session: bool

    @staticmethod
    def run_subtask(input_data_batch, *args, **kwargs) -> List[SubTaskResult]:
        app_id = kwargs["app_id"]
        use_session = kwargs["use_session"]

        session_id = None
        result = []
        for input_data in input_data_batch:
            app = App.objects.get(uuid=app_id)
            request_input_data = {"input": input_data, "stream": False}
            request = RequestFactory().post(f"/api/apps/{app_id}/run", data=request_input_data, format="json")
            request.user = app.owner
            request.data = request_input_data
            response = AppViewSet().run(request=request, uid=app_id, session_id=session_id)
            if response.status_code == 200:
                result.append(SubTaskResult(status=TaskStatus.SUCCESS, output=response.data["output"]))
            else:
                result.append(
                    SubTaskResult(
                        status=TaskStatus.FAILURE,
                        error={"status_code": response.status_code, "data": response.data},
                    )
                )
            if use_session and session_id is None:
                if "session" in response.data:
                    session_id = response.data["session"]["id"]

        return result

    @staticmethod
    def schedule_next_batch(job, start_after_secs):
        job_meta = AppRunTaskRunner.JobMetadata(**job.meta)

        django_rq.get_queue(job_meta.queue_name).enqueue_in(
            datetime.timedelta(seconds=start_after_secs),
            run_subtask,
            args=(
                "app_run",
                job_meta.task_run_log_uuid,
                job_meta.input_data_index + job_meta.batch_size,
                job_meta.batch_size,
                TaskRunner.get_input_data_batch(
                    job_meta.input_data, job_meta.input_data_index + job_meta.batch_size, job_meta.batch_size
                ),
            ),
            kwargs=AppRunTaskRunner.SubTaskArgs(
                app_id=job_meta.app_id,
                use_session=job_meta.use_session,
            ).dict(),
            on_success=on_success_callback,
            on_failure=on_failure_callback,
            meta=job_meta.copy(
                deep=True, update={"input_data_index": job_meta.input_data_index + job_meta.batch_size}
            ).dict(),
            result_ttl=job_meta.result_ttl,
        )


def _schedule_next_batch(task_run_log_uuid, input_data, input_data_index, batch_size, job, *args, **kwargs):
    task_run_log = TaskRunLog.objects.get(uuid=uuid.UUID(task_run_log_uuid))

    if task_run_log.status == "cancelled":
        TaskRunner.update_task_run_log_results(
            task_run_log_uuid,
            input_data_index,
            [
                SubTaskResult(status=TaskStatus.FAILURE, output="Task cancelled by user").dict()
                for _ in range(input_data_index, len(input_data))
            ],
        )
        return

    # If we have any more tasks to run, schedule the next task
    if input_data_index + batch_size < len(input_data):
        time_remaining_to_schedule_next_task = max(
            (settings.TASK_RUN_DELAY - (job.ended_at - job.started_at).total_seconds()), 1
        )

        task_run_type = job.meta.get("task_run_type", None)
        if task_run_type == "app_run":
            AppRunTaskRunner.schedule_next_batch(job, time_remaining_to_schedule_next_task)

    else:
        # All tasks are completed. Update the task status to completed
        task_run_log.status = "succeeded"
        task_run_log.save()


def on_success_callback(job, connection, result, *args, **kwargs):
    TaskRunner.update_task_run_log_results(job.meta["task_run_log_uuid"], job.meta["input_data_index"], result)

    _schedule_next_batch(
        job.meta["task_run_log_uuid"], job.meta["input_data"], job.meta["input_data_index"], job.meta["batch_size"], job
    )


def on_failure_callback(job, connection, type, value, traceback):
    logger.error(
        f'task_run_log_uuid: {job.meta["task_run_log_uuid"]}, type: {type}, value: {value}, Traceback: {traceback} ',
    )
    TaskRunner.update_task_run_log_results(
        job.meta["task_run_log_uuid"],
        job.meta["input_data_index"],
        [
            SubTaskResult(status=TaskStatus.FAILURE, error=f"Exception: {type}, detail: {value}").dict()
            for _ in range(job.meta["batch_size"])
        ],
    )

    _schedule_next_batch(
        job.meta["task_run_log_uuid"], job.meta["input_data"], job.meta["input_data_index"], job.meta["batch_size"], job
    )


def run_subtask(task_run_type, task_run_log_uuid, input_data_index, batch_size, input_data_batch, *args, **kwargs):
    subtask_results = []
    if task_run_type == "app_run":
        subtask_results = AppRunTaskRunner.run_subtask(input_data_batch, *args, **kwargs)

    return list(map(lambda x: x.dict(), subtask_results))


def run_app_task(app_id=None, input_data=None, *args, **kwargs):
    job_metadata = kwargs["_job_metadata"]

    task_run_log_uuid = job_metadata["task_run_log_uuid"]
    batch_size = kwargs.get("batch_size", 1)
    use_session = kwargs.get("use_session", False)
    input_data_index = 0

    result_ttl = 86400

    django_rq.get_queue("default").enqueue(
        run_subtask,
        args=(
            "app_run",
            task_run_log_uuid,
            input_data_index,
            batch_size,
            TaskRunner.get_input_data_batch(input_data, input_data_index, batch_size),
        ),
        kwargs=AppRunTaskRunner.SubTaskArgs(
            app_id=app_id,
            use_session=use_session,
        ).dict(),
        on_success=on_success_callback,
        on_failure=on_failure_callback,
        meta=AppRunTaskRunner.JobMetadata(
            task_run_type="app_run",
            task_run_log_uuid=task_run_log_uuid,
            input_data=input_data,
            input_data_index=input_data_index,
            batch_size=batch_size,
            queue_name="default",
            result_ttl=result_ttl,
            app_id=app_id,
            use_session=use_session,
        ).dict(),
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
                "result_ttl": job.meta["result_ttl"],
            },
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
            "result_ttl": result_ttl,
        },
        result_ttl=result_ttl,
    )

    return [SubTaskResult().dict()] * len(input_data)
