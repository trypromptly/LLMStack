# File generated from our OpenAPI spec by Stainless.

from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional, Union

from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam as OpenAIChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam as OpenAIChatCompletionContentPartParam,
)
from openai.types.chat.chat_completion_function_message_param import (
    ChatCompletionFunctionMessageParam as OpenAIChatCompletionFunctionMessageParam,
)
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam as OpenAIChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam as OpenAIChatCompletionToolMessageParam,
)
from typing_extensions import Literal, Required, TypedDict

__all__ = ["ChatCompletionMessageParam"]


class MimeTypes(Enum):
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_MARKDOWN = "text/markdown"
    TEXT_CSV = "text/csv"
    TEXT_TSV = "text/tab-separated-values"
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_GIF = "image/gif"
    IMAGE_BMP = "image/bmp"
    IMAGE_WEBP = "image/webp"
    IMAGE_SVG = "image/svg+xml"
    IMAGE_TIFF = "image/tiff"
    VIDEO_MP4 = "video/mp4"
    VIDEO_WEBM = "video/webm"
    VIDEO_OGG = "video/ogg"
    AUDIO_WAV = "audio/wav"
    AUDIO_MP3 = "audio/mp3"
    AUDIO_OGG = "audio/ogg"


class ContentPartTextParam(TypedDict, total=False):
    type: Required[Literal["text"]] = "text"
    mime_type: Optional[str] = "text/plain"
    data: Required[str]


class ContentPartFileParam(TypedDict, total=False):
    type: Required[Literal["file"]] = "file"
    mime_type: Optional[str]
    data: Required[str]
    resolution: Optional[str] = None


class ContentPartBlobParam(TypedDict, total=False):
    type: Required[Literal["blob"]] = "blob"
    mime_type: Optional[str]
    data: Required[bytes]
    resolution: Optional[str] = None


class ContentPartToolCallParam(TypedDict, total=False):
    type: Required[Literal["tool_call"]] = "tool_call"
    data: Required[str]


class ContentPartToolResponse(TypedDict, total=False):
    type: Required[Literal["tool_response"]] = "tool_response"
    data: Required[str]


ContentPartParam = Union[
    ContentPartTextParam, ContentPartFileParam, ContentPartBlobParam, ContentPartToolCallParam, ContentPartToolResponse
]


class ChatCompletionUserMessageParam(TypedDict, total=False):
    content: Required[Union[str, Iterable[OpenAIChatCompletionContentPartParam], Iterable[ContentPartParam], None]]
    role: Required[Literal["user"]]


ChatCompletionMessageParam = Union[
    OpenAIChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    OpenAIChatCompletionAssistantMessageParam,
    OpenAIChatCompletionToolMessageParam,
    OpenAIChatCompletionFunctionMessageParam,
]
