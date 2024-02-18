import uuid
from typing import Dict, List, Literal, Optional, Union

import httpx
from openai import resources
from openai._base_client import make_request_options
from openai._streaming import Stream as Stream
from openai._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from openai._utils import maybe_transform, required_args
from openai.pagination import SyncPage
from openai.types import CompletionUsage, chat, completion_create_params

from ._streaming import LLMGRPCStream
from ._utils import _convert_schema_dict_to_gapic, google_finish_reason_to_literal
from .constants import PROVIDER_GOOGLE, PROVIDER_STABILITYAI
from .types import Model


class Completions(resources.Completions):
    @required_args(["messages", "model"], ["messages", "model", "stream"])
    def create(
        self,
        *,
        messages: List[chat.ChatCompletionMessageParam],
        model: Union[
            str,
            Literal[
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
    ) -> Union[chat.ChatCompletion, Stream[chat.ChatCompletionChunk]]:
        if self._client._llm_router_provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=self._client.api_key)
            prompt_tokens = sum([len(message["content"]) / 3 for message in messages])
            if tools:
                google_tools = []
                for tool in tools:
                    import google.ai.generativelanguage as glm

                    google_tools.append(
                        glm.Tool(
                            function_declarations=[
                                glm.FunctionDeclaration(
                                    name=tool["function"]["name"],
                                    description=tool["function"]["description"],
                                    parameters=_convert_schema_dict_to_gapic(
                                        tool["function"]["parameters"],
                                    ),
                                )
                            ]
                        )
                    )
            model_response = genai.GenerativeModel(model, tools=google_tools).generate_content(
                contents=[message["content"] for message in messages],
                generation_config=genai.GenerationConfig(
                    candidate_count=n or 1,
                    stop_sequences=stop or None,
                    max_output_tokens=max_tokens or None,
                    temperature=temperature or None,
                    top_p=top_p or None,
                ),
                stream=stream,
            )

            if stream:

                def process_data(chunk):
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
                            chat.chat_completion_chunk.Choice(
                                index=index,
                                finish_reason=finish_reason,
                                delta=chat.chat_completion_chunk.ChoiceDelta(
                                    content=text, role="assistant", tool_calls=tool_calls
                                ),
                            )
                        )
                        return chat.ChatCompletionChunk(
                            id=str(uuid.uuid4()),
                            choices=choices,
                            model=model,
                            object="chat.completion.chunk",
                            created=0,
                        )

                return LLMGRPCStream(
                    process_data=process_data, grpc_response=model_response, cast_to=chat.ChatCompletionChunk
                )
            choices = []
            outupt_token_count = 0
            for entry in model_response.candidates:
                messages = []
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
                        message=chat.chat_completion_message.ChatCompletionMessage(
                            content=text, role="assistant", tool_calls=tool_calls
                        ),
                    )
                )
            if outupt_token_count == 0:
                outupt_token_count = sum(len(choice.message.content) / 3 for choice in choices)

            return chat.ChatCompletion(
                id=str(uuid.uuid4()),
                choices=choices,
                model=model,
                object="chat.completion",
                created=0,
                usage=CompletionUsage(
                    completion_tokens=outupt_token_count,
                    prompt_tokens=prompt_tokens,
                    total_tokens=outupt_token_count + prompt_tokens,
                ),
            )
        return self._post(
            "/chat/completions",
            body=maybe_transform(
                {
                    "messages": messages,
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
            cast_to=chat.ChatCompletion,
            stream=stream or False,
            stream_cls=Stream[chat.ChatCompletionChunk],
        )


class Chat(resources.Chat):
    pass


class Embeddings(resources.Embeddings):
    pass


class Images(resources.Images):
    pass


class Audio(resources.Audio):
    pass


class Models(resources.Models):
    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        extra_body: Optional[Body] = None,
        timeout: Union[float, httpx.Timeout, None, NotGiven] = NOT_GIVEN,
    ) -> SyncPage[Model]:
        """
        Lists the currently available models, and provides basic information about each
        one such as the owner and availability.
        """
        if self._client._llm_router_provider == PROVIDER_STABILITYAI:
            return self._get_api_list(
                "v1/engines/list",
                page=SyncPage[Model],
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                model=Model,
            )

        elif self._client._llm_router_provider == PROVIDER_GOOGLE:
            import google.generativeai as genai

            genai.configure(api_key=self._client.api_key)
            models = list(
                map(
                    lambda entry: Model(
                        id=entry.name, object="model", created=0, owned_by="", extra_data=entry.__dict__
                    ),
                    list(genai.list_models()),
                )
            )

            return SyncPage(data=models, object="list")

        return self._get_api_list(
            "/models",
            page=SyncPage[Model],
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            model=Model,
        )
