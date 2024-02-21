from openai.resources import AsyncChat as OpenAIAsyncChat
from openai.resources import Chat as OpenAIChat
from openai.resources.chat import ChatWithRawResponse, ChatWithStreamingResponse

from ..._utils import cached_property
from .completions import Completions

__all__ = ["Chat", "AsyncChat"]


class Chat(OpenAIChat):
    @cached_property
    def completions(self) -> Completions:
        return Completions(self._client)

    @cached_property
    def with_raw_response(self) -> ChatWithRawResponse:
        return ChatWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChatWithStreamingResponse:
        return ChatWithStreamingResponse(self)


class AsyncChat(OpenAIAsyncChat):
    pass
