import logging
from typing import Any

from llmstack.apps.app_session_utils import save_app_session_data
from llmstack.jobs.adhoc import HistoryPersistenceJob
from llmstack.play.actor import Actor
from llmstack.play.output_stream import Message, MessageType
from llmstack.processors.tasks import persist_history_task

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
        logger.info("Stopping BookKeepingActor")
        try:
            HistoryPersistenceJob.create(
                func=persist_history_task,
                args=[
                    list(
                        self._processor_configs.keys(),
                    ),
                    self._bookkeeping_data_map,
                ],
            ).add_to_queue()
        except Exception as e:
            logger.error(f"Error adding history persistence job: {e}")
        return super().on_stop()

    def get_dependencies(self):
        return list(
            set([x["template_key"] for x in self._processor_configs.values()]),
        )
