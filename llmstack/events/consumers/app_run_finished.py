import logging

from pydantic import BaseModel

from llmstack.processors.models import RunEntry

logger = logging.getLogger(__name__)


class AppRunFinishedEventData(BaseModel):
    processors: list = []
    bookkeeping_data_map: dict = {}
    usage_metrics: dict = {}

    @property
    def input(self):
        return self.bookkeeping_data_map.get("input", {}).get("run_data", {})

    @property
    def input_request_uuid(self):
        return self.input.get("request_uuid")

    @property
    def input_request_app_uuid(self):
        return self.input.get("request_app_uuid")

    @property
    def input_app_store_uuid(self):
        return self.input.get("request_app_store_uuid")

    @property
    def is_store_request(self):
        return self.input_app_store_uuid is not None

    @property
    def output(self):
        return (
            self.bookkeeping_data_map["agent"].get("run_data", {})
            if "agent" in self.bookkeeping_data_map
            else self.bookkeeping_data_map.get("output", {}).get("run_data", {})
        )

    @property
    def output_timestamp(self):
        return (
            self.bookkeeping_data_map["agent"].get("timestamp")
            if "agent" in self.bookkeeping_data_map
            else self.bookkeeping_data_map.get("output", {}).get("timestamp")
        )

    @property
    def discord_data(self):
        return self.bookkeeping_data_map.get("discord_processor", None)

    @property
    def slack_data(self):
        return self.bookkeeping_data_map.get("slack_processor", None)

    @property
    def twilio_data(self):
        return self.bookkeeping_data_map.get("twilio_processor", None)

    @property
    def platform_data(self):
        if self.discord_data:
            return self.discord_data["run_data"]
        elif self.slack_data:
            return self.slack_data["run_data"]
        elif self.twilio_data:
            return self.twilio_data["run_data"]
        return {}

    @property
    def processor_runs(self):
        processor_runs = []
        for processor in self.processors:
            if processor not in self.bookkeeping_data_map:
                continue
            bookkeeping_data = self.bookkeeping_data_map[processor]
            if isinstance(bookkeeping_data, list):
                processor_runs.extend(
                    [
                        {
                            "endpoint_uuid": processor,
                            "bookkeeping_data": x,
                        }
                        for x in bookkeeping_data
                    ],
                )
                continue
            processor_runs.append(
                {
                    "endpoint_uuid": processor,
                    "bookkeeping_data": bookkeeping_data,
                },
            )
        return sorted(
            processor_runs,
            key=lambda x: x["bookkeeping_data"]["timestamp"],
        )

    @property
    def agent_run(self):
        return self.bookkeeping_data_map.get("agent", None)

    @property
    def request_user_email(self):
        request_user_email = self.input.get("request_user_email")

        if self.slack_data:
            request_user_email = self.slack_data.get("input", {}).get("slack_user_email", None)
        return request_user_email

    @property
    def request_body(self):
        request_body = self.input.get("request_body")
        if self.slack_data:
            request_body = self.input.get("request_body", {}).get("event")
        elif self.discord_data:
            request_body = self.input.get("request_body", {}).get("data")
        return request_body

    @property
    def request_content_type(self):
        return self.input.get("request_content_type")

    @property
    def request_owner_user(self):
        from django.contrib.auth.models import User

        if self.input.get("request_owner"):
            return User.objects.filter(username=self.input["request_owner"]).first()

        return None

    @property
    def request_owner_user_email(self):
        request_owner_user = self.request_owner_user
        if request_owner_user:
            return request_owner_user.email
        return None

    @property
    def request_app_session_key(self):
        return self.input.get("request_app_session_key")

    @property
    def response_body(self):
        response_body = self.output.get("response_body")
        if self.slack_data:
            response_body = self.slack_data.get("input", {}).get("text")
        elif self.discord_data:
            response_body = self.discord_data.get("input", {}).get("text")
        elif self.twilio_data:
            response_body = self.twilio_data.get("input", {}).get("body")
        return response_body

    @property
    def response_headers(self):
        return self.output.get("response_headers")

    @property
    def response_status(self):
        return self.output.get("response_status")

    @property
    def response_content_type(self):
        response_content_type = self.output.get("response_content_type")
        if self.slack_data:
            response_content_type = "text/markdown"
        elif self.discord_data:
            response_content_type = "text/markdown"
        return response_content_type

    @property
    def response_time(self):
        output_timestamp = (
            self.bookkeeping_data_map["agent"]["timestamp"]
            if "agent" in self.bookkeeping_data_map
            else self.bookkeeping_data_map["output"]["timestamp"]
        )
        response_time = output_timestamp - self.bookkeeping_data_map["input"]["timestamp"]
        if self.slack_data:
            response_time = self.slack_data["timestamp"] - self.bookkeeping_data_map["input"]["timestamp"]
        elif self.discord_data:
            response_time = self.discord_data["timestamp"] - self.bookkeeping_data_map["input"]["timestamp"]
        elif self.twilio_data:
            response_time = self.twilio_data["timestamp"] - self.bookkeeping_data_map["input"]["timestamp"]
        return response_time


def persist_app_run_history(event_data: AppRunFinishedEventData):
    processors = event_data.processors
    bookkeeping_data_map = event_data.bookkeeping_data_map

    if "input" not in bookkeeping_data_map or (
        "output" not in bookkeeping_data_map and "agent" not in bookkeeping_data_map
    ):
        logger.error(
            f"Could not persist history {bookkeeping_data_map} for {processors} because input or output is missing",
        )
        return

    run_entry = RunEntry(
        request_uuid=event_data.input_request_uuid,
        app_uuid=event_data.input_request_app_uuid,
        app_store_uuid=event_data.input_app_store_uuid,
        owner=event_data.request_owner_user,
        session_key=event_data.request_app_session_key,
        request_user_email=event_data.request_user_email,
        request_ip=event_data.input.get("request_ip"),
        request_location=event_data.input.get("request_location"),
        request_user_agent=event_data.input.get("request_user_agent", "")[:255],
        request_content_type=event_data.request_content_type,
        request_body=event_data.request_body,
        response_status=event_data.response_status,
        response_body=event_data.response_body,
        response_content_type=event_data.response_content_type,
        response_headers=event_data.response_headers,
        response_time=event_data.response_time,
        platform_data=event_data.platform_data,
    )
    run_entry.save(processor_runs=event_data.processor_runs)
