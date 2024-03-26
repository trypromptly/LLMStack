import logging

from llmstack.processors.models import RunEntry

logger = logging.getLogger(__name__)


def _process_app_run_data(processors, bookkeeping_data_map):
    input = bookkeeping_data_map["input"]["run_data"]
    output = (
        bookkeeping_data_map["agent"]["run_data"]
        if "agent" in bookkeeping_data_map
        else bookkeeping_data_map["output"]["run_data"]
    )

    output_timestamp = (
        bookkeeping_data_map["agent"]["timestamp"]
        if "agent" in bookkeeping_data_map
        else bookkeeping_data_map["output"]["timestamp"]
    )
    discord_data = bookkeeping_data_map["discord_processor"] if "discord_processor" in bookkeeping_data_map else None
    slack_data = bookkeeping_data_map["slack_processor"] if "slack_processor" in bookkeeping_data_map else None
    twilio_data = bookkeeping_data_map["twilio_processor"] if "twilio_processor" in bookkeeping_data_map else None
    platform_data = {}
    if discord_data:
        platform_data = discord_data["run_data"]
    elif slack_data:
        platform_data = slack_data["run_data"]
    elif twilio_data:
        platform_data = twilio_data["run_data"]

    processor_runs = []
    for processor in processors:
        if processor not in bookkeeping_data_map:
            continue
        bookkeeping_data = bookkeeping_data_map[processor]
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
    processor_runs = sorted(
        processor_runs,
        key=lambda x: x["bookkeeping_data"]["timestamp"],
    )

    # Save history
    request_user_email = input["request_user_email"]
    if not request_user_email and slack_data:
        request_user_email = slack_data["input"]["slack_user_email"] or None

    request_body = input["request_body"]
    if slack_data:
        request_body = input["request_body"]["event"]
    elif discord_data:
        request_body = input["request_body"]["data"]

    response_body = output["response_body"]
    response_content_type = output["response_content_type"]
    if slack_data:
        response_body = slack_data["input"]["text"]
        response_content_type = "text/markdown"
    elif discord_data:
        response_body = discord_data["input"]["text"]
        response_content_type = "text/markdown"
    elif twilio_data:
        response_body = twilio_data["input"]["body"]
        response_content_type = "text/markdown"

    response_time = output_timestamp - bookkeeping_data_map["input"]["timestamp"]
    if slack_data:
        response_time = slack_data["timestamp"] - bookkeeping_data_map["input"]["timestamp"]
    elif discord_data:
        response_time = discord_data["timestamp"] - bookkeeping_data_map["input"]["timestamp"]
    elif twilio_data:
        response_time = twilio_data["timestamp"] - bookkeeping_data_map["input"]["timestamp"]

    run_entry = RunEntry(
        request_uuid=input["request_uuid"],
        app_uuid=input["request_app_uuid"] or None,
        app_store_uuid=input.get("request_app_store_uuid", None) or None,
        endpoint_uuid=input["request_endpoint_uuid"] or None,
        owner=input["request_owner"] or None,
        session_key=input["request_app_session_key"] or None,
        request_user_email=request_user_email,
        request_ip=input["request_ip"],
        request_location=input["request_location"],
        request_user_agent=input["request_user_agent"][:255],
        request_content_type=input["request_content_type"],
        request_body=request_body,
        response_status=output["response_status"],
        response_body=response_body,
        response_content_type=response_content_type,
        response_headers=output["response_headers"],
        response_time=response_time,
        processor_runs=processor_runs,
        platform_data=platform_data,
    )
    return input, processor_runs, run_entry, bookkeeping_data_map["agent"] if "agent" in bookkeeping_data_map else None


def persist_app_run_history(event_data):
    processors = event_data.get("processors", [])
    bookkeeping_data_map = event_data.get("bookkeeping_data_map", {})
    if "input" not in bookkeeping_data_map or (
        "output" not in bookkeeping_data_map and "agent" not in bookkeeping_data_map
    ):
        logger.error(
            f"Could not persist history {bookkeeping_data_map} for {processors} because input or output is missing",
        )
        return

    input, processor_runs, run_entry, agent_run = _process_app_run_data(processors, bookkeeping_data_map)
    run_entry.save()
