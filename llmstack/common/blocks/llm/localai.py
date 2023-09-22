import json
import logging
from typing import Dict, List, Optional, Union

from pydantic import Field, confloat, conint
from llmstack.common.blocks.http import HttpAPIProcessorOutput
from llmstack.common.blocks.llm.openai import ChatMessage, FunctionCall, OpenAIAPIProcessor, OpenAIAPIProcessorConfiguration, OpenAIAPIProcessorInput, OpenAIAPIProcessorOutput, OpenAIAPIProcessorOutputMetadata

logger = logging.getLogger(__name__)


class LocalAICompletionsAPIProcessorInput(OpenAIAPIProcessorInput):
    prompt: str


class LocalAICompletionsAPIProcessorOutput(OpenAIAPIProcessorOutput):
    choices: List[str]


class LocalAICompletionsAPIProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    base_url: Optional[str]
    model: str

    max_tokens: Optional[conint(ge=1, le=4096)]

    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)]
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)]
    stream: Optional[bool]

    timeout: Optional[int]


class LocalAICompletionsAPIProcessor(OpenAIAPIProcessor[LocalAICompletionsAPIProcessorInput, LocalAICompletionsAPIProcessorOutput, LocalAICompletionsAPIProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'localai_completions_api_processor'

    def _get_api_url(self) -> dict:
        return '{}/completions'.format(self.configuration.base_url)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: LocalAICompletionsAPIProcessorInput, configuration: LocalAICompletionsAPIProcessorConfiguration) -> dict:
        return {
            'model': configuration.model,
            'prompt': input.prompt,
            'max_tokens': configuration.max_tokens,
            'temperature': configuration.temperature,
            'top_p': configuration.top_p,
            'stream': configuration.stream,
        }

    def _transform_streaming_api_response(self, input: LocalAICompletionsAPIProcessorInput, configuration: LocalAICompletionsAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> LocalAICompletionsAPIProcessorOutput:
        text = response.content.decode('utf-8')
        json_response = json.loads(text.split('data: ')[1])
        choices = list(
            map(lambda x: x.get('text', ''), json_response['choices']),
        )
        return LocalAICompletionsAPIProcessorOutput(choices=choices, metadata=json_response)

    def _transform_api_response(self, input: LocalAICompletionsAPIProcessorInput, configuration: LocalAICompletionsAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> LocalAICompletionsAPIProcessorOutput:
        choices = list(
            map(lambda x: x.get('text', ''),
                json.loads(response.text)['choices']),
        )
        json_response = json.loads(response.text)

        return LocalAICompletionsAPIProcessorOutput(choices=choices, metadata=json_response)


class LocalAIChatCompletionsAPIProcessorInput(OpenAIAPIProcessorInput):
    system_message: Optional[str] = Field(
        ...,
        description='The intial system message to be set.',
    )
    chat_history: List[ChatMessage] = Field(
        default=[
        ], description='The chat history, in the [chat format](/docs/guides/chat/introduction).',
    )
    messages: List[ChatMessage] = Field(
        default=[], description='The messages to be sent to the API.',
    )
    functions: Optional[List[FunctionCall]] = Field(
        default=None,
        description='A list of functions the model may generate JSON inputs for .',
    )


class LocalAIChatCompletionsAPIProcessorOutput(OpenAIAPIProcessorOutput):
    choices: List[ChatMessage] = Field(
        ...,
        description='Chat completions, in the [chat format](/docs/guides/chat/introduction).',
        min_items=1,
    )


class LocalAIChatCompletionsAPIProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    base_url: Optional[str]

    model: str = Field(description='ID of the model to use.',)

    max_tokens: Optional[conint(ge=1, le=32000)] = Field(
        1024,
        description='The maximum number of tokens allowed for the generated answer. By default, the number of tokens the model can return will be (4096 - prompt tokens).\n',
        example=1024,
    )

    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description='What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n',
        example=1,
    )
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)] = Field(
        1,
        description='An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.\n\nWe generally recommend altering this or `temperature` but not both.\n',
        example=1,
    )

    stream: Optional[bool] = False
    function_call: Optional[Union[str, Dict]] = Field(
        default=None,
        description="Controls how the model responds to function calls. \"none\" means the model does not call a function, and responds to the end-user. \"auto\" means the model can pick between an end-user or calling a function. Specifying a particular function via {\"name\":\ \"my_function\"} forces the model to call that function. \"none\" is the default when no functions are present. \"auto\" is the default if functions are present.",
    )


class LocalAIChatCompletionsAPIProcessor(OpenAIAPIProcessor[LocalAIChatCompletionsAPIProcessorInput, LocalAIChatCompletionsAPIProcessorOutput, LocalAIChatCompletionsAPIProcessorConfiguration]):
    def _get_api_url(self) -> str:
        return '{}/chat/completions'.format(self.configuration.base_url)

    def api_url(self) -> str:
        return self._get_api_url()

    @staticmethod
    def name() -> str:
        return 'localai_chat_completions_api_processor'

    def _get_api_request_payload(self, input: LocalAIChatCompletionsAPIProcessorInput, configuration: LocalAIChatCompletionsAPIProcessorConfiguration) -> dict:
        input_json = json.loads(
            input.copy(
                exclude={'env'},
            ).json(),
        )
        configuration_json = json.loads(configuration.json())
        if 'functions' in input_json and (input_json['functions'] is None or len(input_json['functions']) == 0):
            del input_json['functions']
            if 'function_call' in configuration_json:
                del configuration_json['function_call']

        if 'function_call' in configuration_json and configuration_json['function_call'] is None:
            del configuration_json['function_call']

        for message in input_json['messages'] + input_json['chat_history']:
            if 'name' in message and not message['name']:
                del message['name']

            if 'function_call' in message and message['function_call'] is None:
                del message['function_call']

            if 'function_call' in message and 'name' in message['function_call'] and not message['function_call']['name']:
                del message['function_call']

        messages = []
        if input.system_message:
            messages.append(
                {'role': 'system', 'content': input.system_message},
            )

        if input.chat_history and len(input.chat_history) > 0:
            messages += input_json['chat_history']

        messages += input_json['messages']

        request_payload = {
            **configuration_json,
            'messages': messages,
            'user': input.env.user,
        }
        if 'functions' in input_json and input_json['functions'] is not None:
            request_payload['functions'] = input_json['functions']

        return request_payload

    def _transform_streaming_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> LocalAIChatCompletionsAPIProcessorOutput:
        text = response.content.decode('utf-8')
        json_response = json.loads(text.split('data: ')[1])
        choices = list(
            map(lambda x: ChatMessage(**x['delta']), json_response['choices']),
        )

        return LocalAIChatCompletionsAPIProcessorOutput(
            choices=choices, metadata=OpenAIAPIProcessorOutputMetadata(
                raw_response=json_response),
        )

    def _transform_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> LocalAIChatCompletionsAPIProcessorOutput:
        choices = list(
            map(lambda x: ChatMessage(**x['message']),
                json.loads(response.text)['choices']),
        )

        return LocalAIChatCompletionsAPIProcessorOutput(
            choices=choices, metadata=OpenAIAPIProcessorOutputMetadata(
                raw_response=json.loads(response.text)),
        )
