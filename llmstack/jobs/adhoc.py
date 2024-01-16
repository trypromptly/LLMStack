import uuid
import django_rq

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from rq.job import Job
from queue import Queue


class ProcessingJob(Job):
    _use_redis = settings.USE_REMOTE_JOB_QUEUE if hasattr(
        settings, 'USE_REMOTE_JOB_QUEUE') else True

    @property
    def queue_name(self):
        return 'default'

    @property
    def job_queue(self):
        if self._use_redis:
            return django_rq.queues.get_queue(self.queue_name)
        else:
            return Queue()

    @classmethod
    def generate_job_id(self):
        raise NotImplementedError()

    @classmethod
    def get_connection(self):
        if self._use_redis:
            return django_rq.get_connection('default')
        else:
            return 'local'  # Return a dummy connection

    @classmethod
    def create(cls, **kwargs):
        return super().create(
            id=cls.generate_job_id(),
            connection=cls.get_connection(),
            **kwargs)

    def add_to_queue(self, *args, **kwargs) -> Job:
        if self._use_redis:
            queue = django_rq.get_queue(self.queue_name)
            return queue.enqueue_job(job=self)
        else:
            with ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(self.func, *self.args, **self.kwargs)


class DataSourceEntryProcessingJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return '{}'.format(str(uuid.uuid4()))


class HistoryPersistenceJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return '{}'.format(str(uuid.uuid4()))


class ExtractURLJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return '{}'.format(str(uuid.uuid4()))
