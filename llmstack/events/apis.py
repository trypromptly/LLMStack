import datetime
import importlib
import json
import logging
import uuid

from django.conf import settings
from rest_framework import viewsets

from llmstack.jobs.adhoc import ProcessingJob

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        from django.contrib.auth.models import User

        if isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        elif isinstance(o, User):
            return o.username

        return super().default(o)


class EventProcessingJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return "{}".format(str(uuid.uuid4()))


def _get_attr(attr_path):
    if not attr_path:
        return None

    module_name = ".".join(attr_path.split(".")[:-1])
    attr_name = attr_path.split(".")[-1]
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def _process_event_cb(fn_name, event_data_cls, fn_args):
    try:
        # Retrieve the function
        if fn_name:
            event_handler = _get_attr(fn_name)
        else:
            raise ValueError("Function name is required")

        # Retrieve the event data class if provided
        if event_data_cls:
            event_data_cls = _get_attr(event_data_cls)

        # Call the function with appropriate arguments
        if event_handler:
            if event_data_cls:
                event_handler(event_data_cls(**fn_args))
            else:
                event_handler(fn_args)
    except Exception as e:
        # Log errors with detailed information
        logger.error(f"Error processing event {fn_name}: {e}")


class EventsViewSet(viewsets.ViewSet):
    def create(self, topic, event_data):
        event_data_json = {}
        if isinstance(event_data, dict):
            event_data_json = json.loads(json.dumps(event_data, cls=JSONEncoder))
        if topic in settings.EVENT_TOPIC_MAPPING:
            for processor in settings.EVENT_TOPIC_MAPPING[topic]:
                if isinstance(processor, dict):
                    processor_fn_name = processor["event_processor"]
                    processor_event_data_cls = processor.get("event_data_cls")
                    EventProcessingJob.create(
                        func=_process_event_cb, args=[processor_fn_name, processor_event_data_cls, event_data_json]
                    ).add_to_queue()
                elif isinstance(processor, str):
                    processor_fn_name = processor
                    EventProcessingJob.create(
                        func=_process_event_cb, args=[processor_fn_name, None, event_data_json]
                    ).add_to_queue()
