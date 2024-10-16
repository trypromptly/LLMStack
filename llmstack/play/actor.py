import logging
import time
from types import TracebackType
from typing import Any, Optional, Type

from pydantic import BaseModel, model_validator
from pykka import ThreadingActor

from llmstack.play.messages import Message, MessageType
from llmstack.play.output_stream import OutputStream

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

    @model_validator(mode="before")
    def validate_input(cls, values):
        if values.get("input") and not isinstance(values["input"], dict):
            values["input"] = values["input"].model_dump()

        if values.get("config") and not isinstance(values["config"], dict):
            values["config"] = values["config"].model_dump()
        return values


class ActorConfig(BaseModel):
    """
    Configuration for the actor
    """

    name: str
    actor: Type
    kwargs: dict = {}
    dependencies: list = []  # List of actor ids that this actor depends on
    output_template: Optional[str] = None  # Output template for the actor


class Actor(ThreadingActor):
    def __init__(self, id: str, coordinator_urn: str, output_cls: Type = None, dependencies: list = []):
        super().__init__()
        self._id = id
        self._dependencies = dependencies
        self._coordinator_urn = coordinator_urn

        self._messages = {}  # Holds messages while waiting for dependencies
        self._output_stream = OutputStream(
            stream_id=self._id,
            coordinator_urn=self._coordinator_urn,
            output_cls=output_cls,
        )

    def on_receive(self, message: Message) -> Any:
        if message.type == MessageType.ERRORS:
            self.on_error(message.data.errors)
            return

        if message.type == MessageType.CONTENT_STREAM_BEGIN:
            pass

        if message.type == MessageType.CONTENT_STREAM_END:
            pass

        if message.type == MessageType.CONTENT_STREAM_CHUNK:
            self.input_stream({message.sender: message.data.chunk})

        if message.type == MessageType.CONTENT:
            self._messages = {
                **self._messages,
                **{
                    message.sender: (
                        message.data.content.model_dump()
                        if isinstance(message.data.content, BaseModel)
                        else message.data.content
                    )
                },
            }

            # Call input only when all the dependencies are met
            if set(self._dependencies) == set(self._messages.keys()):
                self.input(self._messages)

    def input(self, message: Any) -> Any:
        # Co-ordinator calls this when all the dependencies are met. This
        # should be called only once whether input_stream is used or not
        raise NotImplementedError

    def input_stream(self, message: Any) -> Any:
        # Co-ordinator calls this when any actor in the dependency chain has
        # data
        raise NotImplementedError

    def reset(self):
        # Resets the current state so we can reuse this actor with new input
        self._messages = {}

    @property
    def dependencies(self):
        return []

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

        # TODO: Send error to output stream
