from typing import Any, Iterator, Optional, TypeVar, cast

import httpx
from openai import AsyncStream, Stream
from openai._streaming import ServerSentEvent, SSEDecoder
from openai._utils import is_dict

from .types.chat.chat_completion_chunk import ChatCompletionChunk

_T = TypeVar("_T")


class LLMRestStream(Stream):
    pass


class LLMAnthropicStream(Stream[ChatCompletionChunk]):
    def __init__(
        self,
        *,
        cast_to: type[_T],
        response: httpx.Response,
        client: Any,
    ) -> None:
        self.response = response
        self._cast_to = cast_to
        self._client = client
        self._decoder = SSEDecoder()
        self._iterator = self.__stream__()

    def __next__(self) -> _T:
        return self._iterator.__next__()

    def __iter__(self) -> Iterator[_T]:
        for item in self._iterator:
            yield item

    def _iter_events(self) -> Iterator[ServerSentEvent]:
        yield from self._decoder.iter(self.response.iter_lines())

    def __stream__(self) -> Iterator[_T]:
        cast_to = cast(Any, self._cast_to)
        response = self.response
        process_data = self._client._process_response_data
        iterator = self._iter_events()
        input_tokens = 0
        id = None
        model = None
        output_tokens = 0

        for sse in iterator:
            if sse.event == "completion":
                yield process_data(data=sse.json(), cast_to=cast_to, response=response)

            if (
                sse.event == "message_start"
                or sse.event == "message_delta"
                or sse.event == "message_stop"
                or sse.event == "content_block_start"
                or sse.event == "content_block_delta"
                or sse.event == "content_block_stop"
            ):
                data = sse.json()
                if is_dict(data) and "type" not in data:
                    data["type"] = sse.event

                if data.get("type") == "message_start":
                    id = data.get("message", {"id": None}).get("id")
                    model = data.get("model", None)
                    input_tokens = data.get("message", {}).get("usage", {}).get("input_tokens", 0)
                    continue
                elif data.get("type") == "content_block_start":
                    continue
                elif data.get("type") == "message_stop":
                    continue

                elif data.get("type") == "content_block_delta":
                    if "delta" in data and data["delta"]["type"] == "text_delta":
                        data = {
                            "id": id,
                            "object": "chat.completion.chunk",
                            "created": 0,
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "content": [
                                            {
                                                "type": "text",
                                                "mime_type": "text/plain",
                                                "data": data["delta"]["text"],
                                            }
                                        ],
                                    },
                                    "logprobs": None,
                                    "finish_reason": None,
                                }
                            ],
                        }
                elif data.get("type") == "content_block_stop":
                    data = {
                        "id": id,
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "logprobs": None,
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    continue
                elif data.get("type") == "message_delta":
                    output_tokens += data.get("usage", {}).get("output_tokens", 0)
                    data = {
                        "id": id,
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "logprobs": None,
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                        },
                    }
                else:
                    continue

                yield process_data(data=data, cast_to=cast_to, response=response)

            if sse.event == "ping":
                continue

            if sse.event == "error":
                body = sse.data

                try:
                    body = sse.json()
                    err_msg = f"{body}"
                except Exception:
                    err_msg = sse.data or f"Error code: {response.status_code}"

                raise self._client._make_status_error(
                    err_msg,
                    body=body,
                    response=self.response,
                )

        # Ensure the entire stream is consumed
        for _sse in iterator:
            ...

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        self.close()

    def close(self) -> None:
        """
        Close the response and release the connection.

        Automatically called if the response body is read to completion.
        """
        self.response.close()


class LLMGRPCStream(Stream):
    def __init__(
        self,
        *,
        cast_to: type[_T],
        response: Any,
        client: Any,
        process_data: Any,
    ) -> None:
        self.response = response
        self._cast_to = cast_to
        self._client = client
        self._iterator = self.__stream__()
        self._process_data = process_data

    def __next__(self) -> _T:
        return self._iterator.__next__()

    def __iter__(self) -> Iterator[_T]:
        for item in self._iterator:
            yield item

    def _iter_events(self) -> Iterator[Any]:
        for _ in self.response:
            yield _

    def __stream__(self) -> Iterator[_T]:
        iterator = self._iter_events()

        for entry in iterator:
            yield self._process_data(chunk=entry)

        for _entry in iterator:
            ...

    def __enter__(self):
        return self

    def close(self) -> None:
        """
        Close the response and release the connection.

        Automatically called if the response body is read to completion.
        """
        pass


class LLMAsyncStream(AsyncStream):
    pass
