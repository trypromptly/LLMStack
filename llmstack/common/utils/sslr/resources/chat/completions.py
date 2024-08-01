import base64
import json
import uuid
from typing import Dict, List, Literal, Optional, Union

import httpx
from openai._base_client import make_request_options
from openai.resources.chat import AsyncCompletions as OpenAIAsyncCompletions
from openai.resources.chat import Completions as OpenAICompletions
from openai.resources.chat import (
    CompletionsWithRawResponse,
    CompletionsWithStreamingResponse,
)
from openai.types import chat, completion_create_params

from ..._streaming import (
    LLMAnthropicStream,
    LLMCohereStream,
    LLMGRPCStream,
    LLMRestStream,
    Stream,
)
from ..._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from ..._utils import (
    _convert_schema_dict_to_gapic,
    cached_property,
    convert_google_function_call_args_map_to_dict,
    generate_uuid,
    google_finish_reason_to_literal,
    maybe_transform,
    required_args,
)
from ...constants import (
    PROVIDER_ANTHROPIC,
    PROVIDER_COHERE,
    PROVIDER_CUSTOM,
    PROVIDER_GOOGLE,
    PROVIDER_MISTRAL,
)
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
                "gpt-4o",
                "gpt-4o-mini",
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
        system = None
        path = "/chat/completions"
        stream_cls = LLMRestStream[_chat.ChatCompletionChunk]

        if self._client._llm_router_provider == PROVIDER_GOOGLE:
            return self._invoke_google_rpc(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                n=n,
                seed=seed,
                stop=stop,
                stream=stream,
                temperature=temperature,
                tool_choice=tool_choice,
                tools=tools,
                top_p=top_p,
                user=user,
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

        post_body_data = {
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
        }

        if self._client._llm_router_provider == PROVIDER_ANTHROPIC:
            path = "/messages"
            stream_cls = LLMAnthropicStream[_chat.ChatCompletionChunk]
            user_messages = list(filter(lambda message: message["role"] != "system", messages_openai_format))
            system_messages = list(filter(lambda message: message["role"] == "system", messages_openai_format))
            if system_messages and "content" in system_messages[0] and isinstance(system_messages[0]["content"], str):
                system = system_messages[0]["content"]
                if system:
                    post_body_data["system"] = system

            post_body_data["messages"] = user_messages
            post_body_data.pop("seed")

        elif self._client._llm_router_provider == PROVIDER_COHERE:
            path = "/chat"
            stream_cls = LLMCohereStream[_chat.ChatCompletionChunk]
            user_messages = list(filter(lambda message: message["role"] != "system", messages_openai_format))
            system_messages = list(filter(lambda message: message["role"] == "system", messages_openai_format))
            if system_messages and "content" in system_messages[0] and isinstance(system_messages[0]["content"], str):
                system = system_messages[0]["content"]
                if system:
                    post_body_data["preamble"] = system
            msg = ""
            for message in user_messages:
                if isinstance(message["content"], str):
                    msg += message["content"]
                elif isinstance(message["content"], list):
                    for content_part in message["content"]:
                        if content_part["type"] == "text":
                            msg += content_part["text"]
                else:
                    raise ValueError("Invalid message content")
            post_body_data["message"] = msg
        elif self._client._llm_router_provider == PROVIDER_MISTRAL:
            path = "/chat/completions"
            stream_cls = LLMRestStream[_chat.ChatCompletionChunk]
            post_body_data["random_seed"] = seed
            if extra_body and "safe_prompt" in extra_body:
                post_body_data["safe_prompt"] = extra_body["safe_prompt"]

            if "seed" in post_body_data:
                post_body_data.pop("seed")

        elif self._client._llm_router_provider == PROVIDER_CUSTOM:
            post_body_data["model"] = self._client.deployment_config.model_name

        return self._post(
            path=path,
            body=maybe_transform(
                post_body_data,
                completion_create_params.CompletionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=_chat.ChatCompletion,
            stream=stream or False,
            stream_cls=stream_cls,
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
                parts = []
                tool_calls = []
                tool_call_idx = 0
                for part in content.parts:
                    if part.text:
                        parts.append(
                            {
                                "type": "text",
                                "data": part.text,
                                "mime_type": "text/plain",
                            }
                        )
                    elif part.inline_data:
                        parts.append(
                            {
                                "type": "blob",
                                "data": part.inline_data.data,
                                "mime_type": part.inline_data.mime_type,
                            }
                        )
                    elif part.function_call:
                        call_id = generate_uuid(
                            f"""{part.function_call.name}_{
                            json.dumps(convert_google_function_call_args_map_to_dict(part.function_call.args))}"""
                        )
                        parts.append(
                            {
                                "type": "tool_call",
                                "tool_name": part.function_call.name,
                                "tool_args": json.dumps(
                                    convert_google_function_call_args_map_to_dict(part.function_call.args)
                                ),
                                "id": f"google_call_{call_id}",
                            }
                        )
                        tool_calls.append(
                            chat.chat_completion_message_tool_call.ChatCompletionMessageToolCall(
                                index=tool_call_idx,
                                id=f"google_call_{call_id}",
                                function=chat.chat_completion_message_tool_call.Function(
                                    arguments=json.dumps(
                                        convert_google_function_call_args_map_to_dict(part.function_call.args)
                                    ),
                                    name=part.function_call.name,
                                    type="function",
                                ),
                                type="function",
                            )
                        )
                        tool_call_idx += 1
                choices.append(
                    _chat.chat_completion.Choice(
                        index=index,
                        finish_reason=finish_reason,
                        message=_chat.chat_completion.ChatCompletionMessage(
                            content=parts, role="assistant", tool_calls=tool_calls if tool_calls else None
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
                parts = []
                tool_calls = []
                idx = 0
                tool_call_idx = 0
                for part in content.parts:
                    if part.text:
                        parts.append(
                            {
                                "type": "text",
                                "data": part.text,
                                "mime_type": "text/plain",
                            }
                        )
                    elif part.inline_data:
                        parts.append(
                            {
                                "type": "blob",
                                "data": part.inline_data.data,
                                "mime_type": part.inline_data.mime_type,
                            }
                        )
                    elif part.function_call:
                        call_id = generate_uuid(
                            f"""{part.function_call.name}_{
                            json.dumps(convert_google_function_call_args_map_to_dict(part.function_call.args))}"""
                        )
                        parts.append(
                            {
                                "type": "tool_call",
                                "tool_name": part.function_call.name,
                                "tool_args": json.dumps(
                                    convert_google_function_call_args_map_to_dict(part.function_call.args)
                                ),
                                "id": f"google_call_{call_id}",
                            }
                        )
                        tool_calls.append(
                            _chat.chat_completion_chunk._ChoiceDeltaToolCall(
                                index=tool_call_idx,
                                id=f"google_call_{call_id}",
                                function=chat.chat_completion_chunk.ChoiceDeltaToolCallFunction(
                                    arguments=json.dumps(
                                        convert_google_function_call_args_map_to_dict(part.function_call.args)
                                    ),
                                    name=part.function_call.name,
                                    type="function",
                                ),
                            )
                        )
                        tool_call_idx += 1

                    idx += 1
                choices.append(
                    _chat.chat_completion_chunk.Choice(
                        index=index,
                        finish_reason="tool_calls" if tool_calls else finish_reason,
                        delta=_chat.chat_completion_chunk.ChoiceDelta(
                            content=parts, role="assistant", tool_calls=tool_calls if tool_calls else None
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
        max_tokens: Union[Optional[int], NotGiven] = NOT_GIVEN,
        n: Union[Optional[int], NotGiven] = NOT_GIVEN,
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

                if message["role"] == "user":
                    messages_google_format.append(
                        glm.Content(role="user", parts=parts),
                    )
                elif message["role"] == "assistant":
                    messages_google_format.append(
                        glm.Content(role="model", parts=parts),
                    )

            elif isinstance(message["content"], str):
                if message["role"] == "user":
                    messages_google_format.append(
                        glm.Content(
                            role="user",
                            parts=[glm.Part(text=message["content"])],
                        )
                    )
                elif message["role"] == "assistant":
                    messages_google_format.append(
                        glm.Content(
                            role="model",
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
