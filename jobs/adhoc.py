import uuid

import django_rq
from rq.job import Job


class ProcessingJob(Job):
    @property
    def queue_name(self):
        return 'default'

    @property
    def job_queue(cls):
        return django_rq.queues.get_queue(cls.queue_name)

    @classmethod
    def generate_job_id(self):
        raise NotImplementedError()

    @classmethod
    def get_connection(self):
        return django_rq.get_connection('default')

    @classmethod
    def create(cls, **kwargs):
        return super().create(id=cls.generate_job_id(), connection=cls.get_connection(), **kwargs)

    def add_to_queue(self, *args, **kwargs) -> Job:
        queue = django_rq.get_queue(self.queue_name)
        return queue.enqueue_job(job=self)


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