import json
from typing import Any, Iterator, Optional, TypeVar, cast

import httpx
from openai import APIError, AsyncStream, Stream
from openai._streaming import ServerSentEvent, SSEDecoder
from openai._utils import is_dict, is_mapping

_T = TypeVar("_T")


class LLMRestStream(Stream[_T]):
    def __stream__(self) -> Iterator[_T]:
        cast_to = cast(Any, self._cast_to)
        response = self.response
        process_data = self._client._process_response_data
        iterator = self._iter_events()
        collect_choices = [None] * 100
        id = None
        model = None
        max_choice_idx = 0
        created = 0
        usage_data = {}

        for sse in iterator:
            if sse.data.startswith("[DONE]"):
                choices = [
                    {
                        "delta": {},
                        "index": i,
                        "logprobs": None,
                        "finish_reason": "usage",
                    }
                    for i in range(0, max_choice_idx + 1)
                ]
                yield process_data(
                    data={
                        "id": id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": choices,
                        "usage": {
                            **usage_data,
                            "input_tokens": usage_data.get("prompt_tokens"),
                            "output_tokens": usage_data.get("completion_tokens"),
                        },
                    },
                    cast_to=cast_to,
                    response=response,
                )
                break

            if sse.event is None:
                data = sse.json()
                if is_mapping(data) and data.get("error"):
                    raise APIError(
                        message="An error occurred during streaming",
                        request=self.response.request,
                        body=data["error"],
                    )
                if "id" in data:
                    id = data["id"]
                if "model" in data:
                    model = data["model"]
                if "created" in data:
                    created = data["created"]
                if "choices" in data:
                    for choice in data["choices"]:
                        max_choice_idx = max(max_choice_idx, choice["index"])
                        if choice["index"] is not None:
                            if collect_choices[choice["index"]] is None:
                                collect_choices[choice["index"]] = [choice]
                            else:
                                collect_choices[choice["index"]].append(choice)
                if "usage" in data and data["usage"]:
                    usage_data = data["usage"]
                    continue

                yield process_data(data=data, cast_to=cast_to, response=response)

        # Ensure the entire stream is consumed
        for _sse in iterator:
            ...


class LLMAnthropicStream(Stream[_T]):
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
                                "finish_reason": "usage",
                            }
                        ],
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens,
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


class LLMCohereStream(Stream[_T]):
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
        yield from self.response.iter_lines()

    def __stream__(self) -> Iterator[_T]:
        cast_to = cast(Any, self._cast_to)
        response = self.response
        process_data = self._client._process_response_data
        iterator = self._iter_events()
        input_tokens = 0
        id = None
        model = None
        output_tokens = 0
        total_tokens = 0

        for chunk in iterator:
            chunk_json = json.loads(chunk)
            if chunk_json["event_type"] == "stream-end":
                input_tokens = chunk_json.get("token_count", {}).get("prompt_tokens", 0)
                output_tokens = chunk_json.get("token_count", {}).get("response_tokens", 0)
                total_tokens = chunk_json.get("token_count", {}).get("total_tokens", 0)
                finish_reason = chunk_json.get("finish_reason", "stop")

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
                            "finish_reason": finish_reason,
                        }
                    ],
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    },
                }

            elif chunk_json["event_type"] == "stream-start":
                id = chunk_json.get("generation_id")
                continue

            elif chunk_json["event_type"] == "text-generation":
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
                                        "data": chunk_json["text"],
                                    }
                                ],
                            },
                            "logprobs": None,
                            "finish_reason": None,
                        }
                    ],
                }
            else:
                continue

            yield process_data(data=data, cast_to=cast_to, response=response)

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
