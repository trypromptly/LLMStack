from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from llmstack.common.blocks.base.schema import StrEnum


class MessageType(StrEnum):
    BEGIN = "begin"
    BOOKKEEPING = "bookkeeping"
    CONTENT = "content"
    CONTENT_STREAM_CHUNK = "content_stream_chunk"
    CONTENT_STREAM_BEGIN = "content_stream_begin"
    CONTENT_STREAM_END = "content_stream_end"
    ERRORS = "errors"


class MessageData(BaseModel):
    pass


class Error(BaseModel):
    code: int = -1
    message: str


class ErrorsData(MessageData):
    errors: List[Error]


class ContentData(MessageData):
    content: Any


class ContentStreamChunkData(MessageData):
    chunk: Any


class ContentStreamErrorsData(MessageData):
    errors: List[Error]


class Message(BaseModel):
    id: str
    type: MessageType
    sender: str
    receiver: Optional[str] = None
    reply_to: Optional[str] = None  # Id of the message this is a reply to
    data: Optional[
        Union[
            ContentData,
            ContentStreamChunkData,
            ContentStreamErrorsData,
            ErrorsData,
            Dict,
        ]
    ] = None
