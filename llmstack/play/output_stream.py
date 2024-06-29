"""
This module contains the OutputStream class.
"""

import asyncio
import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Optional, Type

import orjson
from pydantic import BaseModel
from pykka import ActorProxy, ActorRegistry

__all__ = ["OutputStream"]

logger = logging.getLogger(__name__)


def stitch_model_objects(obj1: Any, obj2: Any) -> Any:
    """Stitch two objects together.

    Args:
      obj1: The first object (could be a BaseModel instance, dict, or list).
      obj2: The second object (could be a BaseModel instance, dict, or list).

    Returns:
      The stitched object.
    """
    from llmstack.play.actors.agent import AgentOutput

    if isinstance(obj1, dict) and isinstance(obj2, AgentOutput):
        return {
            **obj1,
            **obj2.model_dump(),
            **{
                "content": stitch_model_objects(
                    obj1.get(
                        "content",
                        {},
                    ),
                    obj2.model_dump().get(
                        "content",
                        {},
                    ),
                ),
            },
        }

    if isinstance(obj1, BaseModel):
        obj1 = obj1.model_dump()
    if isinstance(obj2, BaseModel):
        obj2 = obj2.model_dump()

    def stitch_fields(
        obj1_fields: Dict[str, Any],
        obj2_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        stitched_fields = defaultdict(Any)
        for field in set(obj1_fields).union(obj2_fields):
            stitched_fields[field] = stitch_model_objects(
                obj1_fields.get(field, None),
                obj2_fields.get(field, None),
            )
        return dict(stitched_fields)

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        return stitch_fields(obj1, obj2)

    elif isinstance(obj1, list) and isinstance(obj2, list):
        stitched_obj = []
        for item1, item2 in zip(obj1, obj2):
            stitched_obj.append(stitch_model_objects(item1, item2))
        return stitched_obj

    elif isinstance(obj1, str) and isinstance(obj2, str):
        return obj1 + obj2

    else:
        return obj2 if obj2 else obj1


class MessageType(str, Enum):
    """
    MessageType enum.
    """

    BEGIN = "begin"
    BOOKKEEPING = ("bookkeeping",)
    BOOKKEEPING_DONE = "bookkeeping_done"
    INPUT = "input"
    TOOL_INVOKE = "tool_invoke"
    AGENT_DONE = "agent_done"
    STREAM = "stream"
    STREAM_CLOSED = "stream_closed"
    STREAM_ERROR = "stream_error"
    STREAM_DATA = "stream_data"
    STREAM_FINALIZED = "stream_finalized"
    STREAM_FINALIZED_ERROR = "stream_finalized_error"
    STREAM_FINALIZED_DATA = "stream_finalized_data"
    STREAM_FINALIZED_CLOSED = "stream_finalized_closed"
    STREAM_FINALIZED_CLOSED_ERROR = "stream_finalized_closed_error"
    STREAM_FINALIZED_CLOSED_DATA = "stream_finalized_closed_data"

    def __str__(self):
        return self.value


class Message(BaseModel):
    message_id: Optional[str] = None
    message_type: MessageType = MessageType.BEGIN
    message_from: Optional[str] = None
    message_to: Optional[str] = None
    response_to: Optional[str] = None  # This is used to send a response to a message
    message: Optional[Any] = None
    template_key: Optional[str] = None


class StreamClosedException(Exception):
    pass


class OutputStream:
    """
    OutputStream class.
    """

    class Status:
        OPEN = "open"
        CLOSED = "closed"

    def __init__(
        self,
        stream_id: str = None,
        coordinator_urn: str = None,
        output_cls: Type = None,
    ) -> None:
        """
        Initializes the OutputStream class.
        """
        self._data = None
        self._output_cls = output_cls
        self._stream_id = stream_id
        self._coordinator_urn = coordinator_urn
        self._coordinator_proxy = None
        self._message_id = None
        self._response_to = None
        self._status: OutputStream.Status = OutputStream.Status.OPEN

    @property
    def _coordinator(self) -> ActorProxy:
        """
        Returns the coordinator.
        """
        if not self._coordinator_proxy:
            try:
                self._coordinator_proxy = ActorRegistry.get_by_urn(
                    self._coordinator_urn,
                ).proxy()
            except Exception as e:
                logger.error(f"Failed to get coordinator proxy: {e}")

        return self._coordinator_proxy

    def set_message_id(self, message_id: str) -> None:
        """
        Sets the current message id.
        """
        self._message_id = message_id

    def set_response_to(self, response_to: str) -> None:
        """
        Sets the response to.
        """
        self._response_to = response_to

    async def write(self, data: BaseModel, message_id=None, message_to=None, response_to=None) -> None:
        """
        Stitches fields from data to _data.
        """
        if self._status == OutputStream.Status.CLOSED:
            raise StreamClosedException("Output stream is closed.")

        self._coordinator.relay(
            Message(
                message_id=message_id or self._message_id,
                message_type=MessageType.STREAM_DATA,
                message_from=self._stream_id,
                message=(
                    orjson.loads(data.json())
                    if isinstance(
                        data,
                        BaseModel,
                    )
                    else data
                ),
                message_to=message_to,
                response_to=response_to or self._response_to,
            ),
        )

        if self._data is None:
            self._data = (
                data.model_dump()
                if isinstance(
                    data,
                    BaseModel,
                )
                else data
            )
        else:
            self._data = stitch_model_objects(self._data, data)
        await asyncio.sleep(0.0001)

    async def write_raw(self, message: Message) -> None:
        """
        Writes raw message to the output stream.
        """
        if self._status == OutputStream.Status.CLOSED:
            raise StreamClosedException("Output stream is closed.")

        self._coordinator.relay(message)

        await asyncio.sleep(0.0001)

    def close(self) -> None:
        """
        Closes the output stream.
        """
        self._status = OutputStream.Status.CLOSED

    def get_data(self) -> BaseModel:
        """
        Returns the data.
        """
        return self._data

    def get_status(self) -> Status:
        """
        Returns the status.
        """
        return self._status

    def finalize(
        self,
        message_id=None,
        message_to=None,
        response_to=None,
    ) -> BaseModel:
        """
        Closes the output stream and returns stitched data.
        """
        output = self._data
        self._data = None

        self._coordinator.relay(
            Message(
                message_id=message_id or self._message_id,
                message_to=message_to,
                message_type=MessageType.STREAM_CLOSED,
                message_from=self._stream_id,
                message=(
                    orjson.loads(output.json())
                    if isinstance(
                        output,
                        BaseModel,
                    )
                    else output
                ),
                response_to=response_to or self._response_to,
            ),
        )

        return output if not self._output_cls else self._output_cls(**output)

    def bookkeep(self, data: BaseModel) -> None:
        """
        Bookkeeping entry.
        """
        self._coordinator.relay(
            Message(
                message_type=MessageType.BOOKKEEPING,
                message_from=self._stream_id,
                message=data.model_dump(),
                message_id=self._message_id,
            ),
        )

    def bookkeep_done(self) -> None:
        """
        Bookkeeping done.
        """
        try:
            self._coordinator.relay(
                Message(
                    message_type=MessageType.BOOKKEEPING_DONE,
                    message_from=self._stream_id,
                    message=None,
                ),
            )
        except Exception as e:
            # Coordinator may have already stopped
            logger.info(f"Error sending bookkeeping done message: {e}")

    def error(self, error: Exception) -> None:
        """
        Error entry.
        """
        self._coordinator.relay(
            Message(
                message_type=MessageType.STREAM_ERROR,
                message_from=self._stream_id,
                message=str(error),
            ),
        )
