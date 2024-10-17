"""
This module contains the OutputStream class.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Any, Dict, Type

from pydantic import BaseModel
from pykka import ActorProxy, ActorRegistry

from llmstack.play.messages import (
    ContentData,
    ContentStreamChunkData,
    ContentStreamErrorsData,
    Error,
    Message,
    MessageType,
    ToolCallResponseData,
)

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


class OutputStream:
    """
    OutputStream class.
    """

    def __init__(
        self,
        stream_id: str = None,
        coordinator_urn: str = None,
        output_cls: Type = None,
    ) -> None:
        """
        Initializes the OutputStream class.
        """
        self._message_id = str(uuid.uuid4())
        self._data = None
        self._output_cls = output_cls
        self._stream_id = stream_id
        self._coordinator_urn = coordinator_urn
        self._coordinator_proxy = None

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
                logger.error(f"Failed to get coordinator proxy for {self._coordinator_urn}: {e}")

        return self._coordinator_proxy

    async def write(self, data: Any) -> None:
        """
        Stitches fields from data to _data.
        """

        self._coordinator.relay(
            Message(
                id=self._message_id,
                type=MessageType.CONTENT_STREAM_CHUNK,
                sender=self._stream_id,
                receiver="coordinator",
                data=ContentStreamChunkData(
                    chunk=(
                        data.model_dump()
                        if isinstance(
                            data,
                            BaseModel,
                        )
                        else data
                    ),
                ),
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
        self._coordinator.relay(message)

        await asyncio.sleep(0.0001)

    def get_data(self) -> BaseModel:
        """
        Returns the data.
        """
        return self._data

    def finalize(
        self,
    ) -> BaseModel:
        """
        Closes the output stream and returns stitched data.
        """
        output = self._data if not self._output_cls else self._output_cls(**self._data)
        self._data = None

        # Send the end message
        self._coordinator.relay(
            Message(
                id=self._message_id,
                type=MessageType.CONTENT_STREAM_END,
                sender=self._stream_id,
                receiver="coordinator",
            ),
        )

        # Send the final data

        self._coordinator.relay(
            Message(
                id=self._message_id,
                type=MessageType.CONTENT,
                sender=self._stream_id,
                receiver="coordinator",
                data=ContentData(
                    content=(
                        output.model_dump()
                        if isinstance(
                            output,
                            BaseModel,
                        )
                        else output
                    ),
                ),
            ),
        )

        return output

    def bookkeep(self, data: BaseModel) -> None:
        """
        Bookkeeping entry.
        """
        self._coordinator.relay(
            Message(
                id=self._message_id,
                type=MessageType.BOOKKEEPING,
                sender=self._stream_id,
                receiver="output",
                data=data.model_dump(),
            ),
        )

    def error(self, error: Exception) -> None:
        """
        Error entry.
        """
        self._coordinator.relay(
            Message(
                type=MessageType.ERRORS,
                sender=self._stream_id,
                receiver="coordinator",
                data=ContentStreamErrorsData(errors=[Error(message=str(error))]),
            ),
        )

    def send_tool_call_response(self, reply_to: str, data: ToolCallResponseData) -> None:
        """
        Sends the tool call response.
        """
        self._coordinator.relay(
            Message(
                id=self._message_id,
                type=MessageType.TOOL_CALL_RESPONSE,
                sender=self._stream_id,
                receiver="agent",
                reply_to=reply_to,
                data=data,
            )
        )
