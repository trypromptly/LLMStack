import logging
from typing import Any

from llmstack.apps.app_session_utils import save_app_session_data
from llmstack.events.apis import EventsViewSet
from llmstack.play.actor import Actor
from llmstack.play.output_stream import Message, MessageType

logger = logging.getLogger(__name__)


class BookKeepingActor(Actor):
    def __init__(
        self,
        output_stream,
        processor_configs,
        dependencies=[],
        all_dependencies=[],
        is_agent=False,
        **kwargs,
    ):
        super().__init__(dependencies=dependencies, all_dependencies=all_dependencies)
        self._processor_configs = processor_configs
        self._output_stream = output_stream
        self._bookkeeping_data_map = {}
        self._is_agent = is_agent

    def on_receive(self, message: Message) -> Any:
        if message.message_type == MessageType.BOOKKEEPING:
            if message.message_id:
                self._bookkeeping_data_map[message.message_from] = (
                    self._bookkeeping_data_map[message.message_from]
                    + [
                        message.message,
                    ]
                    if message.message_from in self._bookkeeping_data_map
                    else [message.message]
                )
            else:
                self._bookkeeping_data_map[message.message_from] = message.message

            # Save session data
            processor_config = (
                self._processor_configs[message.message_from]
                if message.message_from in self._processor_configs
                else None
            )
            if processor_config and "app_session_data" in processor_config and processor_config["app_session_data"]:
                processor_config["app_session_data"]["data"] = message.message["session_data"]
                save_app_session_data(processor_config["app_session_data"])

            # Persist history
            if (
                len(self._bookkeeping_data_map)
                == len(
                    self.dependencies,
                )
                and not self._is_agent
            ):
                self._output_stream.bookkeep_done()

        if message.message_type == MessageType.AGENT_DONE:
            self._output_stream.bookkeep_done()

    def on_stop(self) -> None:
        usage_metrics = {}
        logger.info("Stopping BookKeepingActor")
        try:
            # Persist only if all the values in the bookkeeping data have disable_history set to False
            if all(
                [
                    "disable_history" in self._bookkeeping_data_map[x]
                    and self._bookkeeping_data_map[x]["disable_history"]
                    for x in list(filter(lambda x: x in self._bookkeeping_data_map, self._processor_configs.keys()))
                ]
                + [
                    "input" in self._bookkeeping_data_map
                    and "disable_history" in self._bookkeeping_data_map["input"]
                    and self._bookkeeping_data_map["input"]["disable_history"]
                ]
            ):
                logger.info("Not persisting history since disable_history is set to True")
                return super().on_stop()

            try:
                for entry in self._bookkeeping_data_map:
                    data = self._bookkeeping_data_map[entry]
                    if isinstance(data, list):
                        for data_element in data:
                            if entry not in usage_metrics:
                                usage_metrics[entry] = []
                            for usage_metric_entry in data_element.get("usage_data", {}).get("usage_metrics", []):
                                usage_metrics[entry].append(usage_metric_entry)
                    elif isinstance(data, dict):
                        usage_metrics[entry] = data.get("usage_data", {}).get("usage_metrics", [])

            except Exception:
                logger.exception("Error getting usage metrics")
                usage_metrics = {}

            EventsViewSet().create(
                "app.run.finished",
                {
                    "processors": list(self._processor_configs.keys()),
                    "bookkeeping_data_map": self._bookkeeping_data_map,
                    "usage_metrics": usage_metrics,
                },
            )
        except Exception as e:
            logger.error(f"Error adding history persistence job: {e}")
        return super().on_stop()
