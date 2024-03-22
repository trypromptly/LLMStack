import importlib
import logging
import uuid

from django.conf import settings
from rest_framework import viewsets

from llmstack.jobs.adhoc import ProcessingJob

logger = logging.getLogger(__name__)


class EventProcessingJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return "{}".format(str(uuid.uuid4()))


class EventsViewSet(viewsets.ViewSet):
    def create(self, topic, event_data):
        if topic in settings.EVENT_TOPIC_MAPPING:
            for processor_fn_name in settings.EVENT_TOPIC_MAPPING[topic]:
                module_name = ".".join(processor_fn_name.split(".")[:-1])
                fn_name = processor_fn_name.split(".")[-1]
                module = importlib.import_module(module_name)
                fn = getattr(module, fn_name)

                EventProcessingJob.create(func=fn, args=[event_data]).add_to_queue()
