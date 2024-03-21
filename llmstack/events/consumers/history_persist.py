import logging

from llmstack.processors.tasks import _process_app_run_data

logger = logging.getLogger(__name__)


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

    input, processor_runs, run_entry = _process_app_run_data(processors, bookkeeping_data_map)
    run_entry.save()
