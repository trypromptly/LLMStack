import importlib
import logging

from django.conf import settings
from pydantic import BaseModel
from rest_framework import serializers

from llmstack.apps.models import App
from llmstack.processors.models import RunEntry

logger = logging.getLogger(__name__)


def update_billing(*args, **kwargs):
    pass


class MetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunEntry
        fields = ["request_uuid", "app_uuid", "app_store_uuid", "owner", "request_user_email"]


class AppRunFinishedEventData(BaseModel):
    bookkeeping_data_map: dict = {}
    usage_metrics: dict = {}
    request_data: dict = {}
    output: dict = {}

    @property
    def request_uuid(self):
        return self.request_data.get("request_id")

    @property
    def request_app_uuid(self):
        return self.request_data.get("app_uuid")

    @property
    def request_session_id(self):
        return self.request_data.get("session_id")

    @property
    def request_user_email(self):
        return self.request_data.get("request_user_email")

    @property
    def request_ip(self):
        return self.request_data.get("request_ip", "")

    @property
    def request_location(self):
        return self.request_data.get("request_location", "")

    @property
    def request_user_agent(self):
        return self.request_data.get("request_user_agent", "")

    @property
    def request_content_type(self):
        return self.request_data.get("request_content_type", "")

    @property
    def response_status(self):
        if self.output and self.output.get("output"):
            return 200
        return 400

    #     return self.request_data.get("id", "")
    @property
    def request_body(self):
        return self.bookkeeping_data_map.get("_inputs0", {}).get("input", {})

    @property
    def response_body(self):
        if self.output:
            return self.output.get("output") or ""

    @property
    def is_store_request(self):
        return self.request_data.get("type") in ["platform", "app_store"]

    @property
    def response_time(self):
        timestamps = list(map(lambda entry: entry.get("timestamp"), self.bookkeeping_data_map.values()))
        # Sort timestamps in ascending order and return the difference between the first and last timestamps
        timestamps = [t for t in timestamps if t is not None]
        timestamps = sorted(timestamps)
        if len(timestamps) < 2:
            return 0  # Return 0 if there are not enough valid timestamps
        return timestamps[-1] - timestamps[0]

    @property
    def processor_runs(self):
        data = []
        for key, value in self.bookkeeping_data_map.items():
            data.append({"processor_id": key, "bookkeeping_data": value})
        return data


def persist_app_run_history(event_data: AppRunFinishedEventData):
    owner = App.objects.get(uuid=event_data.request_app_uuid).owner if event_data.request_app_uuid else None

    run_entry = RunEntry(
        request_uuid=event_data.request_uuid,
        app_uuid=event_data.request_app_uuid,
        app_store_uuid=None,
        owner=owner,
        session_key=event_data.request_session_id,
        request_user_email=event_data.request_user_email,
        request_ip=event_data.request_ip,
        request_location=event_data.request_location,
        request_user_agent=event_data.request_user_agent[:255],
        request_content_type=event_data.request_content_type,
        request_body=event_data.request_body,
        response_status=event_data.response_status,
        response_body=event_data.response_body,
        response_content_type="text/markdown",
        response_headers={},
        response_time=event_data.response_time,
        platform_data=event_data.request_data,
        usage_metrics=dict(
            map(
                lambda key: (key, event_data.usage_metrics[key].get("usage_metrics", [])),
                event_data.usage_metrics.keys(),
            )
        ),
    )
    # Save History
    run_entry.save(processor_runs=event_data.processor_runs)

    module_name = ".".join(settings.UPDATE_BILLING_FUNC.split(".")[:-1])
    func_name = settings.UPDATE_BILLING_FUNC.split(".")[-1]
    module = importlib.import_module(module_name)
    update_billing_func = getattr(module, func_name)
    update_billing_func(
        usage_metrics=event_data.usage_metrics,
        usage_data=MetadataSerializer(run_entry).data,
        user_email=owner.email if owner else event_data.request_user_email,
    )
