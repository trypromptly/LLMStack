import base64
import uuid
from typing import Dict, List, Literal, Optional, Union

import httpx
from openai._base_client import make_request_options
from openai._compat import cached_property
from openai._streaming import Stream as Stream
from openai._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from openai._utils import maybe_transform
from openai.resources.chat import AsyncCompletions as OpenAIAsyncCompletions
from openai.resources.chat import Completions as OpenAICompletions
from openai.resources.chat import (
    CompletionsWithRawResponse,
    CompletionsWithStreamingResponse,
)
from openai.types import chat, completion_create_params

from ..._streaming import LLMGRPCStream
from ..._utils import (
    _convert_schema_dict_to_gapic,
    google_finish_reason_to_literal,
    required_args,
)
from ...constants import PROVIDER_GOOGLE
from ...types import chat as _chat
from ...types.chat.chat_completion_message_param import ChatCompletionMessageParam

__all__ = ["Completions", "AsyncCompletions"]


class Completions(OpenAICompletions):
    @cached_property
    def with_raw_response(self) -> CompletionsWithRawResponse:
        return CompletionsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CompletionsWithStreamingResponse:
        return CompletionsWithStreamingResponse(self)

    @required_args(["messages", "model"], ["messages", "model", "stream"])
    def create(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        model: Union[
            str,
            Literal[
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
                "gpt-4-1106-preview",
                "gpt-4-vision-preview",
                "gpt-4",
                "gpt-4-0314",
                "gpt-4-0613",
                "gpt-4-32k",
                "gpt-4-32k-0314",
                "gpt-4-32k-0613",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-3.5-turbo-0301",
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-1106",
                "gpt-3.5-turbo-0125",
                "gpt-3.5-turbo-16k-0613",
            ],
        ],
        frequency_penalty: Union[Optional[float], NotGiven] = NOT_GIVEN,
        function_call: Union[chat.completion_create_params.FunctionCall, NotGiven] = NOT_GIVEN,
        functions: Union[List[chat.completion_create_params.Function], NotGiven] = NOT_GIVEN,
        logit_bias: Union[Optional[Dict[str, int]], NotGiven] = NOT_GIVEN,
        max_tokens: Union[Optional[int], NotGiven] = NOT_GIVEN,
        n: Union[Optional[int], NotGiven] = NOT_GIVEN,
        presence_penalty: Union[Optional[float], NotGiven] = NOT_GIVEN,
        response_format: Union[chat.completion_create_params.ResponseFormat, NotGiven] = NOT_GIVEN,
        seed: Union[Optional[int], NotGiven] = NOT_GIVEN,
        stop: Union[Optional[str], List[str], NotGiven] = NOT_GIVEN,
        stream: Union[Literal[False], Literal[True], NotGiven] = NOT_GIVEN,
        temperature: Union[Optional[float], NotGiven] = NOT_GIVEN,
        tool_choice: Union[chat.ChatCompletionToolChoiceOptionParam, NotGiven] = NOT_GIVEN,
        tools: Union[List[chat.ChatCompletionToolParam], NotGiven] = NOT_GIVEN,
        top_p: Union[Optional[float], NotGiven] = NOT_GIVEN,
        user: Union[str, NotGiven] = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        extra_body: Optional[Body] = None,
        timeout: Union[float, httpx.Timeout, None, NotGiven] = NOT_GIVEN,
    ) -> Union[_chat.ChatCompletion, Stream[_chat.ChatCompletionChunk]]:
        if self._client._llm_router_provider == PROVIDER_GOOGLE:
            return self._invoke_google_rpc(
                model=model,
                messages=messages,
                stream=stream,
            )

        messages_openai_format = []

        for message in messages:
            if message["role"] == "user":
                if isinstance(message["content"], list):
                    parts = []
                    for part in message["content"]:
                        if "mime_type" in part:
                            if part["type"] == "text":
                                parts.append({"text": part["data"], "type": "text"})
                            elif part["type"] == "file":
                                if part["mime_type"].startswith("image"):
                                    parts.append(
                                        {
                                            "image_url": {
                                                "url": part["data"],
                                                "detail": part["resolution"],
                                            },
                                            "type": "image_url",
                                        }
                                    )
                            elif part["type"] == "blob":
                                if part["mime_type"].startswith("image"):
                                    parts.append(
                                        {
                                            "image_url": {
                                                "url": f"data:{part['mime_type']};base64,{base64.b64encode(part['data']).decode('utf-8')}",
                                                "detail": part["resolution"],
                                            },
                                            "type": "image_url",
                                        }
                                    )
                        else:
                            parts.append(part)

                    messages_openai_format.append(
                        {
                            "role": "user",
                            "content": parts,
                        }
                    )
                else:
                    messages_openai_format.append(message)
            else:
                messages_openai_format.append(message)

        return self._post(
            "/chat/completions",
            body=maybe_transform(
                {
                    "messages": messages_openai_format,
                    "model": model,
                    "frequency_penalty": frequency_penalty,
                    "function_call": function_call,
                    "functions": functions,
                    "logit_bias": logit_bias,
                    "max_tokens": max_tokens,
                    "n": n,
                    "presence_penalty": presence_penalty,
                    "response_format": response_format,
                    "seed": seed,
                    "stop": stop,
                    "stream": stream,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_p": top_p,
                    "user": user,
                },
                completion_create_params.CompletionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=_chat.ChatCompletion,
            stream=stream or False,
            stream_cls=Stream[_chat.ChatCompletionChunk],
        )

    def _process_rpc_response(self, response, model, stream):
        def _transform_grpc_response(model_response):
            choices = []
            outupt_token_count = 0
            for entry in model_response.candidates:
                index = entry.index
                content = entry.content
                finish_reason = google_finish_reason_to_literal(entry.finish_reason)
                outupt_token_count += entry.token_count
                parts = content.parts
                text = ""
                tool_calls = []
                for part in parts:
                    if part.text:
                        text += part.text
                    elif part.inline_data:
                        # Add a data url to text
                        text += f"data:{part.inline_data.mime_type};base64,{part.inline_data.data}"
                    elif part.function_call:
                        tool_calls.append(
                            chat.chat_completion_message.FunctionCall(
                                arguments=part.function_call.args, name=part.function_call.name
                            )
                        )

                choices.append(
                    chat.chat_completion.Choice(
                        index=index,
                        finish_reason=finish_reason,
                        message=_chat.chat_completion.ChatCompletionMessage(
                            content=text, role="assistant", tool_calls=tool_calls
                        ),
                    )
                )

            return _chat.ChatCompletion(
                id=str(uuid.uuid4()),
                choices=choices,
                model=model,
                object="chat.completion",
                created=0,
            )

        def _transform_streaming_grpc_response(chunk):
            choices = []
            for entry in chunk.candidates:
                index = entry.index
                content = entry.content
                finish_reason = google_finish_reason_to_literal(entry.finish_reason)
                parts = content.parts
                text = ""
                tool_calls = []
                idx = 0
                for part in parts:
                    if part.text:
                        text += part.text
                    elif part.inline_data:
                        # Add a data url to text
                        text += f"data:{part.inline_data.mime_type};base64,{part.inline_data.data}"
                    elif part.function_call:
                        tool_calls.append(
                            chat.chat_completion_chunk.ChoiceDeltaToolCall(
                                index=idx,
                                function=chat.chat_completion_chunk.ChoiceDeltaToolCallFunction(
                                    arguments=part.function_call.args, name=part.function_call.name
                                ),
                                type="function",
                            )
                        )
                    idx += 1
                choices.append(
                    _chat.chat_completion_chunk.Choice(
                        index=index,
                        finish_reason=finish_reason,
                        delta=chat.chat_completion_chunk.ChoiceDelta(
                            content=text, role="assistant", tool_calls=tool_calls
                        ),
                    )
                )
                return _chat.ChatCompletionChunk(
                    id=str(uuid.uuid4()),
                    choices=choices,
                    model=model,
                    object="chat.completion.chunk",
                    created=0,
                )

        if stream:
            return LLMGRPCStream(
                cast_to=_chat.ChatCompletionChunk,
                response=response,
                client=self._client,
                process_data=_transform_streaming_grpc_response,
            )

        return _transform_grpc_response(response)

    def _invoke_google_rpc(
        self,
        model: str,
        messages: List[ChatCompletionMessageParam],
        frequency_penalty: Union[Optional[float], NotGiven] = NOT_GIVEN,
        function_call: Union[chat.completion_create_params.FunctionCall, NotGiven] = NOT_GIVEN,
        functions: Union[List[chat.completion_create_params.Function], NotGiven] = NOT_GIVEN,
        logit_bias: Union[Optional[Dict[str, int]], NotGiven] = NOT_GIVEN,
        max_tokens: Union[Optional[int], NotGiven] = NOT_GIVEN,
        n: Union[Optional[int], NotGiven] = NOT_GIVEN,
        presence_penalty: Union[Optional[float], NotGiven] = NOT_GIVEN,
        response_format: Union[chat.completion_create_params.ResponseFormat, NotGiven] = NOT_GIVEN,
        seed: Union[Optional[int], NotGiven] = NOT_GIVEN,
        stop: Union[Optional[str], List[str], NotGiven] = NOT_GIVEN,
        stream: Union[Literal[False], Literal[True], NotGiven] = NOT_GIVEN,
        temperature: Union[Optional[float], NotGiven] = NOT_GIVEN,
        tool_choice: Union[chat.ChatCompletionToolChoiceOptionParam, NotGiven] = NOT_GIVEN,
        tools: Union[List[chat.ChatCompletionToolParam], NotGiven] = NOT_GIVEN,
        top_p: Union[Optional[float], NotGiven] = NOT_GIVEN,
        user: Union[str, NotGiven] = NOT_GIVEN,
    ):
        google_tools = None
        messages_google_format = []

        import google.ai.generativelanguage as glm
        import google.generativeai as genai

        genai.configure(api_key=self._client.api_key)
        if tools:
            google_tools = list(
                map(
                    lambda tool: glm.Tool(
                        glm.Tool(
                            function_declarations=[
                                glm.FunctionDeclaration(
                                    name=tool["function"]["name"],
                                    description=tool["function"]["description"],
                                    parameters=_convert_schema_dict_to_gapic(tool["function"]["parameters"]),
                                )
                            ]
                        )
                    ),
                    tools,
                )
            )

        for message in messages:
            if isinstance(message["content"], list):
                parts = []
                for part in message["content"]:
                    if "mime_type" in part:
                        if part["type"] == "text":
                            parts.append(glm.Part(text=part["data"]))
                        elif part["type"] == "file":
                            if part["data"].startswith("http"):
                                data_bytes = httpx.get(part["data"]).content
                                parts.append(
                                    glm.Part(inline_data=glm.Blob(mime_type=part["mime_type"], data=data_bytes))
                                )
                            elif part["data"].startswith("data"):
                                parts.append(
                                    glm.Part(
                                        inline_data=glm.Blob(
                                            mime_type=part["mime_type"],
                                            data=base64.b64decode(part["data"].split(",")[1]),
                                        )
                                    )
                                )
                            else:
                                raise ValueError("Invalid file data")
                        elif part["type"] == "blob":
                            parts.append(glm.Part(inline_data=glm.Blob(mime_type=part["mime_type"], data=part["data"])))

                messages_google_format.append(
                    glm.Content(role="user" if message["role"] == "user" else "model", parts=parts)
                )

            elif isinstance(message["content"], str):
                messages_google_format.append(
                    glm.Content(
                        role="user" if message["role"] == "user" else "model",
                        parts=[glm.Part(text=message["content"])],
                    )
                )
            else:
                raise ValueError("Invalid message content")

        model_response = genai.GenerativeModel(model, tools=google_tools).generate_content(
            contents=messages_google_format,
            generation_config=genai.GenerationConfig(
                candidate_count=n or 1,
                stop_sequences=stop or None,
                max_output_tokens=max_tokens or None,
                temperature=temperature or None,
                top_p=top_p or None,
            ),
            stream=stream,
        )
        return self._process_rpc_response(model_response, model, stream)


class AsyncCompletions(OpenAIAsyncCompletions):
    pass
