import logging
import time
import uuid
from types import TracebackType
from typing import Any, Type

from pydantic import BaseModel
from pykka import ThreadingActor

from llmstack.play.output_stream import Message, MessageType

logger = logging.getLogger(__name__)


class BookKeepingData(BaseModel):
    """
    Bookkeeping entry
    """

    input: dict = {}
    config: dict = {}
    output: dict = {}
    session_data: dict = {}
    timestamp: float = time.time()
    run_data: dict = {}
    message_id: str = None
    disable_history: bool = False
    usage_data: dict = {}


class ActorConfig(BaseModel):
    """
    Configuration for the actor
    """

    class Config:
        arbitrary_types_allowed = True

    name: str
    template_key: str = ""  # This is used to find other actors dependent on this actor
    actor: Type
    kwargs: dict = {}
    dependencies: list = []
    output_cls: Type = None


class Actor(ThreadingActor):
    def __init__(self, dependencies: list = [], all_dependencies: list = []):
        super().__init__()
        self._dependencies = dependencies
        self._all_dependencies = all_dependencies
        self._messages = {}  # Holds messages while waiting for dependencies

    def on_receive(self, message: Message) -> Any:
        if message.message_type == MessageType.BEGIN:
            self.input(message.message)

        message_and_key = (
            {
                message.template_key: message.message,
            }
            if message.template_key
            else message.message
        )

        if message.message_type == MessageType.STREAM_ERROR:
            self.on_error(message_and_key)
            return

        if message.message_type == MessageType.STREAM_DATA:
            self.input_stream(message_and_key)

        if message.message_type == MessageType.STREAM_CLOSED:
            self._messages = {**self._messages, **message_and_key}

        # Call input only when all the dependencies are met
        if message.message_type == MessageType.STREAM_CLOSED and set(
            self.dependencies,
        ) == set(self._messages.keys()):
            self.input(self._messages)

        # If the message is for a tool, call the tool
        if message.message_type == MessageType.TOOL_INVOKE:
            self._output_stream.set_message_id(str(uuid.uuid4()))
            self._output_stream.set_response_to(message.message_id)
            self.invoke(message.message)

    def input(self, message: Any) -> Any:
        # Co-ordinator calls this when all the dependencies are met. This
        # should be called only once whether input_stream is used or not
        raise NotImplementedError

    def input_stream(self, message: Any) -> Any:
        # Co-ordinator calls this when any actor in the dependency chain has
        # data
        raise NotImplementedError

    def get_dependencies(self):
        # Return a list of template_keys that this actor depends on
        # TODO: This should be persisted in the endpoint or app config
        return []

    @property
    def dependencies(self):
        return list(
            filter(
                lambda x: x in self._all_dependencies,
                list(set(self._dependencies + self.get_dependencies())),
            ),
        )

    def on_error(self, error: Any) -> None:
        # Co-ordinator calls this when any actor in the dependency chain has
        # error
        pass

    def on_stop(self) -> None:
        return super().on_stop()

    def on_failure(
        self,
        exception_type: type[BaseException],
        exception_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        logger.error(
            f"Encountered {exception_type} in {type(self)}({self.actor_urn}): {exception_value}",
        )

        # Send error to output stream
        self._output_stream.error(exception_value)
