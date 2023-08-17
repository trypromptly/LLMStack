import json
import logging
from enum import Enum
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Union

from pydantic import confloat
from pydantic import conint
from pydantic import Extra
from pydantic import Field

from common.blocks.http import BearerTokenAuth, NoAuth
from common.blocks.http import HttpAPIProcessor
from common.blocks.http import HttpAPIProcessorInput
from common.blocks.http import HttpAPIProcessorOutput
from common.blocks.http import JsonBody
from common.blocks.http import RawRequestBody
from common.blocks.base.processor import BaseConfiguration
from common.blocks.base.processor import BaseConfigurationType
from common.blocks.http import HttpAPIError as BaseError
from common.blocks.base.processor import BaseInput
from common.blocks.base.processor import BaseInputEnvironment
from common.blocks.base.processor import BaseInputType
from common.blocks.base.processor import BaseOutput
from common.blocks.base.processor import BaseOutputType
from common.blocks.llm import LLMBaseProcessor
from common.blocks.base.processor import Schema

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 120


def process_openai_error_response(response: HttpAPIProcessorOutput) -> str:
    """
        Processes the error response from OpenAI
    """
    if response.content_json:
        if 'error' in response.content_json:
            if 'message' in response.content_json['error']:
                return response.content_json['error']['message']
            return response.content_json['error']
        elif 'message' in response.content_json:
            return response.content_json['message']
    else:
        return response.text


class OpenAIAPIInputEnvironment(BaseInputEnvironment):
    openai_api_key: Optional[str] = Field(..., description='OpenAI API Key')
    user: Optional[str] = Field(default='', description='User')


class OpenAIAPIProcessorOutputMetadata(Schema):
    raw_response: dict = Field(
        {}, description='The raw response from the API',
    )
    is_cached: bool = Field(
        False, description='Whether the response was served from cache',
    )


class OpenAIAPIProcessorInput(BaseInput):

    env: Optional[OpenAIAPIInputEnvironment] = Field(
        ..., description='Environment variables',
    )


class OpenAIAPIProcessorConfiguration(BaseConfiguration):
    pass


class OpenAIAPIProcessorOutput(BaseOutput):
    metadata: Optional[OpenAIAPIProcessorOutputMetadata]


class OpenAIAPIError(BaseError):
    message: str


class OpenAIAPIProcessor(LLMBaseProcessor[BaseInputType, BaseOutputType, BaseConfigurationType]):
    BASE_URL = 'https://api.openai.com/v1'

    @property
    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration) -> dict:
        raise NotImplementedError()

    def _get_api_url(self) -> dict:
        raise NotImplementedError()

    def _transform_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> BaseOutputType:
        raise NotImplementedError()

    def _process_iter(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration) -> Generator[HttpAPIProcessorOutput, None, None]:
        """
            Invokes the API processor on the input and returns output iterator
        """
        http_api_processor = HttpAPIProcessor({'timeout': DEFAULT_TIMEOUT})
        http_input = HttpAPIProcessorInput(
            url=self._get_api_url(),
            method='POST',
            body=JsonBody(
                json_body=(self._get_api_request_payload(input, configuration)),
            ),
            headers={},
            authorization=BearerTokenAuth(token=input.env.openai_api_key) if input.env.openai_api_key else NoAuth(),
        )

        http_status_is_ok = True
        error_message = ''
        for http_response in http_api_processor.process_iter(
                http_input.dict(),
        ):
            if http_response.is_ok:
                if http_response.text == 'data: [DONE]':
                    return
                else:
                    response = self._transform_streaming_api_response(
                        input, configuration, http_response,
                    )
                    yield response
            else:
                http_status_is_ok = False
                error_message += http_response.text

        if not http_status_is_ok:
            raise Exception(
                process_openai_error_response(
                http_response.copy(update={'content_json': json.loads(error_message)}),
                ),
            )

    def _process(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration) -> HttpAPIProcessorOutput:
        """
            Invokes the API processor on the input and returns the output
        """
        http_api_processor = HttpAPIProcessor({'timeout': DEFAULT_TIMEOUT})
        http_input = HttpAPIProcessorInput(
            url=self._get_api_url(),
            method='POST',
            body=JsonBody(
                json_body=(self._get_api_request_payload(input, configuration)),
            ),
            headers={},
            authorization=BearerTokenAuth(token=input.env.openai_api_key) if input.env.openai_api_key else NoAuth(),
        )

        http_response = http_api_processor.process(
            http_input.dict(),
        )

        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            response = self._transform_api_response(
                input, configuration, http_response,
            )
            return response
        else:
            raise Exception(process_openai_error_response(http_response))


class OpenAICompletionsAPIProcessorInput(OpenAIAPIProcessorInput):
    prompt: str = Field(default='', description='The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.\n\nNote that <|endoftext|> is the document separator that the model sees during training, so if a prompt is not specified the model will generate as if from the beginning of a new document.')


class OpenAICompletionsAPIProcessorOutput(OpenAIAPIProcessorOutput):
    choices: List[str] = Field(
        default=[], description='The list of generated completions.',
    )


class CompletionsModel(str, Enum):
    TEXT_DAVINCI_003 = 'text-davinci-003'
    TEXT_DAVINCI_002 = 'text-davinci-002'
    TEXT_CURIE_001 = 'text-curie-001'
    TEXT_BABBAGE_001 = 'text-babbage-001'
    TEXT_ADA_001 = 'text-ada-001'

    def __str__(self):
        return self.value


class OpenAICompletionsAPIProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    model: CompletionsModel = Field(
        default=CompletionsModel.TEXT_DAVINCI_003,
        description='ID of the model to use. You can use the [List models](/docs/api-reference/models/list) API to see all of your available models, or see our [Model overview](/docs/models/overview) for descriptions of them.',
    )
    suffix: Optional[str] = Field(
        None,
        description='The suffix that comes after a completion of inserted text.',
        example='test.',
    )
    max_tokens: Optional[conint(ge=1, le=4096)] = Field(
        1024,
        description="The maximum number of [tokens](/tokenizer) to generate in the completion.\n\nThe token count of your prompt plus `max_tokens` cannot exceed the model's context length. Most models have a context length of 2048 tokens (except for the newest models, which support 4096).\n",
        example=1024,
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description='What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n',
        example=1,
    )
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)] = Field(
        default=1,
        description='An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.\n\nWe generally recommend altering this or `temperature` but not both.\n',
        example=1,
    )
    n: Optional[conint(ge=1, le=128)] = Field(
        1,
        description='How many completions to generate for each prompt.\n\n**Note:** Because this parameter generates many completions, it can quickly consume your token quota. Use carefully and ensure that you have reasonable settings for `max_tokens` and `stop`.\n',
        example=1,
    )
    stream: Optional[bool] = Field(
        False,
        description='Whether to stream back partial progress. If set, tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message.\n',
    )
    logprobs: Optional[conint(ge=0, le=5)] = Field(
        None,
        description='Include the log probabilities on the `logprobs` most likely tokens, as well the chosen tokens. For example, if `logprobs` is 5, the API will return a list of the 5 most likely tokens. The API will always return the `logprob` of the sampled token, so there may be up to `logprobs+1` elements in the response.\n\nThe maximum value for `logprobs` is 5. If you need more than this, please contact us through our [Help center](https://help.openai.com) and describe your use case.\n',
    )
    echo: Optional[bool] = Field(
        False, description='Echo back the prompt in addition to the completion\n',
    )
    stop: Optional[Union[str, List[str]]] = Field(
        None,
        description='Up to 4 sequences where the API will stop generating further tokens. The returned text will not contain the stop sequence.\n',
    )
    presence_penalty: Optional[confloat(ge=-2.0, le=2.0)] = Field(
        0,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.\n\n[See more information about frequency and presence penalties.](/docs/api-reference/parameter-details)\n",
    )
    frequency_penalty: Optional[confloat(ge=-2.0, le=2.0)] = Field(
        0,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.\n\n[See more information about frequency and presence penalties.](/docs/api-reference/parameter-details)\n",
    )
    best_of: Optional[conint(ge=0, le=20)] = Field(
        1,
        description='Generates `best_of` completions server-side and returns the "best" (the one with the highest log probability per token). Results cannot be streamed.\n\nWhen used with `n`, `best_of` controls the number of candidate completions and `n` specifies how many to return – `best_of` must be greater than `n`.\n\n**Note:** Because this parameter generates many completions, it can quickly consume your token quota. Use carefully and ensure that you have reasonable settings for `max_tokens` and `stop`.\n',
    )
    logit_bias: Optional[Dict[str, Any]] = Field(
        {},
        description='Modify the likelihood of specified tokens appearing in the completion.\n\nAccepts a json object that maps tokens (specified by their token ID in the GPT tokenizer) to an associated bias value from -100 to 100. You can use this [tokenizer tool](/tokenizer?view=bpe) (which works for both GPT-2 and GPT-3) to convert text to token IDs. Mathematically, the bias is added to the logits generated by the model prior to sampling. The exact effect will vary per model, but values between -1 and 1 should decrease or increase likelihood of selection; values like -100 or 100 should result in a ban or exclusive selection of the relevant token.\n\nAs an example, you can pass `{"50256": -100}` to prevent the <|endoftext|> token from being generated.\n',
    )


"""
    OpenAICompletionsAPIProcessor processor class for OpenAI Completions API
"""


class OpenAICompletionsAPIProcessor(OpenAIAPIProcessor[OpenAICompletionsAPIProcessorInput, OpenAICompletionsAPIProcessorOutput, OpenAICompletionsAPIProcessorConfiguration]):

    @staticmethod
    def name() -> str:
        return 'openai_completions_api_processor'

    def _get_api_url(self) -> dict:
        return '{}/completions'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: OpenAICompletionsAPIProcessorInput, configuration: OpenAICompletionsAPIProcessorConfiguration) -> dict:
        return {
            'model': configuration.model,
            'prompt': input.prompt,
            'suffix': configuration.suffix,
            'max_tokens': configuration.max_tokens,
            'temperature': configuration.temperature,
            'top_p': configuration.top_p,
            'n': configuration.n,
            'stream': configuration.stream,
            'logprobs': configuration.logprobs,
            'echo': configuration.echo,
            'stop': configuration.stop,
            'presence_penalty': configuration.presence_penalty,
            'frequency_penalty': configuration.frequency_penalty,
            'best_of': configuration.best_of,
            'logit_bias': configuration.logit_bias,
            'user': input.env.user,
        }

    def _transform_streaming_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> OpenAICompletionsAPIProcessorOutput:
        text = response.content.decode('utf-8')
        json_response = json.loads(text.split('data: ')[1])
        choices = list(
            map(lambda x: x['text'], json_response['choices']),
        )
        return OpenAICompletionsAPIProcessorOutput(
            choices=choices, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json_response),
        )

    def _transform_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> OpenAICompletionsAPIProcessorOutput:
        choices = list(
            map(lambda x: x['text'], json.loads(response.text)['choices']),
        )
        return OpenAICompletionsAPIProcessorOutput(
            choices=choices, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(response.text)),
        )


class Role(str, Enum):
    system = 'system'
    user = 'user'
    assistant = 'assistant'
    function = 'function'

    def __str__(self):
        return self.value


class FunctionCall(Schema):
    name: str = Field(
        default='', description='The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.',
    )
    description: Optional[str] = Field(
        default=None, description='The description of what the function does.',
    )
    parameters: Optional[Dict[Any, Any]] = Field(
        default=None, description='The parameters the functions accepts, described as a JSON Schema object. See the guide for examples, and the JSON Schema reference for documentation about the format.',
    )


class ChatMessage(Schema):
    role: Optional[Role] = Field(
        default=None, description='The role of the author of this message.',
    )
    content: Optional[str] = Field(
        default=None,
        description='The contents of the message',
    )
    name: Optional[str] = Field(
        default=None,
        description='The name of the author of this message. name is required if role is function, and it should be the name of the function whose response is in the content. May contain a-z, A-Z, 0-9, and underscores, with a maximum length of 64 characters.',
    )
    function_call: Optional[Dict] = Field(
        default=None,
        description='The name and arguments of a function that should be called, as generated by the model.',
    )


class OpenAIChatCompletionsAPIProcessorInput(OpenAIAPIProcessorInput):
    system_message: Optional[str] = Field(
        ...,
        description='The intial system message to be set.',
    )
    chat_history: List[ChatMessage] = Field(
        default=[], description='The chat history, in the [chat format](/docs/guides/chat/introduction).',
    )
    messages: List[ChatMessage] = Field(
        default=[], description='The messages to be sent to the API.',
    )
    functions: Optional[List[FunctionCall]] = Field(
        default=None,
        description='A list of functions the model may generate JSON inputs for .',
    )


class OpenAIChatCompletionsAPIProcessorOutput(OpenAIAPIProcessorOutput):
    choices: List[ChatMessage] = Field(
        ...,
        description='Chat completions, in the [chat format](/docs/guides/chat/introduction).',
        min_items=1,
    )


class ChatCompletionsModel(str, Enum):
    GPT_4 = 'gpt-4'
    GPT_3_5 = 'gpt-3.5-turbo'
    GPT_3_5_16K = 'gpt-3.5-turbo-16k'
    GPT_4_0613 = 'gpt-4-0613'
    GPT_3_5_0613 = 'gpt-3.5-turbo-0613'

    def __str__(self):
        return self.value


class OpenAIChatCompletionsAPIProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    model: ChatCompletionsModel = Field(
        default=ChatCompletionsModel.GPT_3_5,
        description='ID of the model to use. Currently, only `gpt-3.5-turbo` and `gpt-4` are supported.',
    )
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
    n: Optional[conint(ge=1, le=128)] = Field(
        1,
        description='How many chat completion choices to generate for each input message.',
        example=1,
    )
    stop: Optional[Union[str, List[str]]] = Field(
        None,
        description='Up to 4 sequences where the API will stop generating further tokens.\n',
    )
    presence_penalty: Optional[confloat(ge=-2.0, le=2.0, multiple_of=0.1)] = Field(
        0,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.\n\n[See more information about frequency and presence penalties.](/docs/api-reference/parameter-details)\n",
    )
    frequency_penalty: Optional[confloat(ge=-2.0, le=2.0, multiple_of=0.1)] = Field(
        0,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.\n\n[See more information about frequency and presence penalties.](/docs/api-reference/parameter-details)\n",
    )
    logit_bias: Optional[Dict[str, Any]] = Field(
        {},
        description='Modify the likelihood of specified tokens appearing in the completion.\n\nAccepts a json object that maps tokens (specified by their token ID in the tokenizer) to an associated bias value from -100 to 100. Mathematically, the bias is added to the logits generated by the model prior to sampling. The exact effect will vary per model, but values between -1 and 1 should decrease or increase likelihood of selection; values like -100 or 100 should result in a ban or exclusive selection of the relevant token.\n',
    )
    stream: Optional[bool] = False
    function_call: Optional[Union[str, Dict]] = Field(
        default=None,
        description="Controls how the model responds to function calls. \"none\" means the model does not call a function, and responds to the end-user. \"auto\" means the model can pick between an end-user or calling a function. Specifying a particular function via {\"name\":\ \"my_function\"} forces the model to call that function. \"none\" is the default when no functions are present. \"auto\" is the default if functions are present.",
    )


class OpenAIChatCompletionsAPIProcessor(OpenAIAPIProcessor[OpenAIChatCompletionsAPIProcessorInput, OpenAIChatCompletionsAPIProcessorOutput, OpenAIChatCompletionsAPIProcessorConfiguration]):
    def _get_api_url(self) -> str:
        return '{}/chat/completions'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    @staticmethod
    def name() -> str:
        return 'openai_chat_completions_api_processor'

    def _get_api_request_payload(self, input: OpenAIChatCompletionsAPIProcessorInput, configuration: OpenAIChatCompletionsAPIProcessorConfiguration) -> dict:
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

    def _transform_streaming_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> OpenAICompletionsAPIProcessorOutput:
        text = response.content.decode('utf-8')
        json_response = json.loads(text.split('data: ')[1])
        choices = list(
            map(lambda x: ChatMessage(**x['delta']), json_response['choices']),
        )

        return OpenAIChatCompletionsAPIProcessorOutput(
            choices=choices, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json_response),
        )

    def _transform_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> OpenAIChatCompletionsAPIProcessorOutput:
        choices = list(
            map(lambda x: ChatMessage(**x['message']), json.loads(response.text)['choices']),
        )

        return OpenAIChatCompletionsAPIProcessorOutput(
            choices=choices, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(response.text)),
        )


class Size(str, Enum):
    field_256x256 = '256x256'
    field_512x512 = '512x512'
    field_1024x1024 = '1024x1024'

    def __str__(self):
        return self.value


class ResponseFormat(str, Enum):
    url = 'url'
    b64_json = 'b64_json'

    def __str__(self):
        return self.value


class OpenAIImageGenerationsProcessorInput(OpenAIAPIProcessorInput):
    prompt: str = Field(
        ...,
        description='A text description of the desired image(s). The maximum length is 1000 characters.',
        example='A cute baby sea otter',
    )


class OpenAIImageGenerationsProcessorOutput(OpenAIAPIProcessorOutput):
    answer: List[str] = Field(
        default=[], description='The generated images.',
    )


class OpenAIImageGenerationsProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    n: Optional[conint(ge=1, le=4)] = Field(
        1,
        description='The number of images to generate. Must be between 1 and 10.',
        example=1,
    )
    size: Optional[Size] = Field(
        '1024x1024',
        description='The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.',
        example='1024x1024',
    )
    response_format: Optional[ResponseFormat] = Field(
        'url',
        description='The format in which the generated images are returned. Must be one of `url` or `b64_json`.',
        example='url',
    )


class OpenAIImageGenerationsProcessor(OpenAIAPIProcessor[OpenAIImageGenerationsProcessorInput, OpenAIImageGenerationsProcessorOutput, OpenAIImageGenerationsProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'openai_image_generations_processor'

    def _get_api_url(self) -> str:
        return '{}/images/generations'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: OpenAIImageGenerationsProcessorInput, configuration: OpenAIImageGenerationsProcessorConfiguration) -> dict:
        return {
            'prompt': input.prompt,
            'n': configuration.n,
            'size': configuration.size,
            'response_format': configuration.response_format,
            'user': input.env.user,
        }

    def _transform_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> OpenAIImageGenerationsProcessorOutput:
        def image_uri(data):
            if 'url' in data:
                return data['url']
            elif 'b64_json' in data:
                return 'data:image/png;base64,{}'.format(data['b64_json'])
            else:
                raise Exception('Invalid response format')

        answer = list(
            map(image_uri, json.loads(response.text)['data']),
        )
        return OpenAIImageGenerationsProcessorOutput(
            answer=answer, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(response.text)),
        )


class OpenAIFile(Schema):
    name: str = Field(description='The name of the file.')
    content: bytes = Field(description='The content of the file.')
    mime_type: str = Field(description='The MIME type of the file.')


class OpenAIImageEditsProcessorInput(OpenAIAPIProcessorInput):
    image: OpenAIFile = Field(
        ...,
        description='The image to edit. Must be a valid PNG file, less than 4MB, and square. If mask is not provided, image must have transparency, which will be used as the mask.',
    )
    mask: Optional[OpenAIFile] = Field(
        None,
        description='An additional image whose fully transparent areas (e.g. where alpha is zero) indicate where `image` should be edited. Must be a valid PNG file, less than 4MB, and have the same dimensions as `image`.',
    )
    prompt: str = Field(
        ...,
        description='A text description of the desired image(s). The maximum length is 1000 characters.',
        example='A cute baby sea otter wearing a beret',
    )


class OpenAIImageEditsProcessorOutput(OpenAIAPIProcessorOutput):
    answer: List[str] = Field(default=[], description='The generated images.')


class OpenAIImageEditsProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    n: Optional[conint(ge=1, le=10)] = Field(
        1,
        description='The number of images to generate. Must be between 1 and 10.',
        example=1,
    )
    size: Optional[Size] = Field(
        '1024x1024',
        description='The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.',
        example='1024x1024',
    )
    response_format: Optional[ResponseFormat] = Field(
        'url',
        description='The format in which the generated images are returned. Must be one of `url` or `b64_json`.',
        example='url',
    )


class OpenAIImageEditsProcessor(OpenAIAPIProcessor[OpenAIImageEditsProcessorInput, OpenAIImageEditsProcessorOutput, OpenAIImageEditsProcessorConfiguration]):
    def _get_api_url(self) -> str:
        return '{}/images/edits'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: OpenAIImageEditsProcessorInput, configuration: OpenAIImageEditsProcessorConfiguration) -> dict:
        configuration_json = json.loads(configuration.json())
        return {
            'image': input.image,
            'mask': input.mask,
            'prompt': input.prompt,
            'user': input.env.user,
            **configuration_json,
        }

    def _transform_api_response(self, input: OpenAIImageEditsProcessorInput, configuration: OpenAIImageEditsProcessorConfiguration, response: HttpAPIProcessorOutput) -> BaseOutputType:
        def image_uri(data):
            if 'url' in data:
                return data['url']
            elif 'b64_json' in data:
                return 'data:image/png;base64,{}'.format(data['b64_json'])
            else:
                raise Exception('Invalid response format')

        answer = list(
            map(image_uri, json.loads(response.text)['data']),
        )
        return OpenAIImageVariationsProcessorOutput(
            answer=answer, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(response.text)),
        )

    def _process(self, input: OpenAIImageEditsProcessorInput, configuration: OpenAIImageEditsProcessorConfiguration) -> BaseOutputType:
        """
            Invokes the API processor on the input and returns the output
        """
        http_api_processor = HttpAPIProcessor({'timeout': DEFAULT_TIMEOUT})
        files = []

        files.append(
            ('image', (input.image.name, input.image.content, input.image.mime_type)),
        )

        http_response = http_api_processor.process(
            HttpAPIProcessorInput(
                url=self._get_api_url(),
                method='POST',
                body=RawRequestBody(
                    data=self._get_api_request_payload(input, configuration), files=files,
                ),
                headers={},
                authorization=BearerTokenAuth(token=input.env.openai_api_key),
            ).dict(),
        )

        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            response = self._transform_api_response(
                input, configuration, http_response,
            )
            return response
        else:
            raise Exception(process_openai_error_response(http_response))


class OpenAIImageVariationsProcessorInput(OpenAIAPIProcessorInput):
    image: OpenAIFile = Field(
        ...,
        description='The image to use as the basis for the variation(s). Must be a valid PNG file, less than 4MB, and square.',
    )


class OpenAIImageVariationsProcessorOutput(OpenAIAPIProcessorOutput):
    answer: List[str] = Field(
        default=[], description='The generated images.',
    )


class OpenAIImageVariationsProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    n: Optional[conint(ge=1, le=10)] = Field(
        1,
        description='The number of images to generate. Must be between 1 and 10.',
        example=1,
    )
    size: Optional[Size] = Field(
        '1024x1024',
        description='The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.',
        example='1024x1024',
    )
    response_format: Optional[ResponseFormat] = Field(
        'url',
        description='The format in which the generated images are returned. Must be one of `url` or `b64_json`.',
        example='url',
    )


class OpenAIImageVariationsProcessor(OpenAIAPIProcessor[OpenAIImageVariationsProcessorInput, OpenAIImageVariationsProcessorOutput, OpenAIImageVariationsProcessorConfiguration]):
    def _get_api_url(self) -> str:
        return '{}/images/variations'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: OpenAIImageVariationsProcessorInput, configuration: OpenAIImageVariationsProcessorConfiguration) -> dict:
        configuration_json = json.loads(configuration.json())
        return {
            'image': input.image,
            'user': input.env.user,
            **configuration_json,
        }

    def _transform_api_response(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> OpenAIImageGenerationsProcessorOutput:
        def image_uri(data):
            if 'url' in data:
                return data['url']
            elif 'b64_json' in data:
                return 'data:image/png;base64,{}'.format(data['b64_json'])
            else:
                raise Exception('Invalid response format')

        answer = list(
            map(image_uri, json.loads(response.text)['data']),
        )
        return OpenAIImageVariationsProcessorOutput(
            answer=answer, metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(response.text)),
        )

    def _process(self, input: OpenAIImageVariationsProcessorInput, configuration: OpenAIImageVariationsProcessorConfiguration) -> BaseOutputType:
        """
            Invokes the API processor on the input and returns the output
        """
        http_api_processor = HttpAPIProcessor({'timeout': DEFAULT_TIMEOUT})

        files = []
        files.append(
            ('image', (input.image.name, input.image.content, 'application/octet-stream')),
        )

        http_response = http_api_processor.process(
            HttpAPIProcessorInput(
                url=self._get_api_url(),
                method='POST',
                body=RawRequestBody(
                    data=self._get_api_request_payload(input, configuration), files=files,
                ),
                headers={},
                authorization=BearerTokenAuth(token=input.env.openai_api_key),
            ).dict(),
        )

        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            response = self._transform_api_response(
                input, configuration, http_response,
            )
            return response
        else:
            raise Exception(process_openai_error_response(http_response))


class InputItem(Schema):
    __root__: List[Any]


class OpenAIEmbeddingsProcessorInput(OpenAIAPIProcessorInput):
    class Config:
        extra = Extra.forbid

    input: Union[str, List[str], List[int], List[InputItem]] = Field(
        ...,
        description='Input text to get embeddings for, encoded as a string or array of tokens. To get embeddings for multiple inputs in a single request, pass an array of strings or array of token arrays. Each input must not exceed 8192 tokens in length.\n',
        example='The quick brown fox jumped over the lazy dog',
    )


class Datum2(Schema):
    embedding: List[float]


class OpenAIEmbeddingsProcessorOutput(OpenAIAPIProcessorOutput):
    data: List[Datum2]


class OpenAIEmbeddingsProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    model: str = Field(
        ...,
        description='ID of the model to use. You can use the [List models](/docs/api-reference/models/list) API to see all of your available models, or see our [Model overview](/docs/models/overview) for descriptions of them.',
    )


class OpenAIEmbeddingsProcessor(OpenAIAPIProcessor[OpenAIEmbeddingsProcessorInput, OpenAIEmbeddingsProcessorOutput, OpenAIEmbeddingsProcessorConfiguration]):
    def _get_api_url(self) -> str:
        return '{}/embeddings'.format(super()._get_api_url())

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: OpenAIEmbeddingsProcessorInput, configuration: OpenAIEmbeddingsProcessorConfiguration) -> dict:
        return {
            'model': configuration.model,
            'inputs': input.inputs,
            'outputs': input.outputs,
            'examples': input.examples,
            'user': input.env.user,
        }


class OpenAIAudioTranscriptionsProcessorInput(OpenAIAPIProcessorInput):
    file: OpenAIFile = Field(
        ...,
        description='The audio file to transcribe, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.\n',
    )

    prompt: Optional[str] = Field(
        None,
        description="An optional text to guide the model's style or continue a previous audio segment. The [prompt](/docs/guides/speech-to-text/prompting) should match the audio language.\n",
    )
    language: Optional[str] = Field(
        None,
        description='The language of the input audio. Supplying the input language in [ISO-639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) format will improve accuracy and latency.\n',
    )


class OpenAIAudioTranscriptionsProcessorOutput(OpenAIAPIProcessorOutput):
    text: str = Field(description='The transcript of the audio file.\n')


class OpenAIAudioTranscriptionsProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    model: str = Field(
        default='whisper-1',
        description='ID of the model to use. Only `whisper-1` is currently available.\n',
    )
    response_format: Optional[str] = Field(
        'json',
        description='The format of the transcript output, in one of these options: json, text, srt, verbose_json, or vtt.\n',
    )
    temperature: Optional[float] = Field(
        0,
        description='The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log_probability) to automatically increase the temperature until certain thresholds are hit.\n',
    )


class OpenAIAudioTranscriptionProcessor(OpenAIAPIProcessor[OpenAIAudioTranscriptionsProcessorInput, OpenAIAudioTranscriptionsProcessorOutput, OpenAIAudioTranscriptionsProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'openai_audio_transcription_processor'

    def _get_api_url(self) -> str:
        return '{}/audio/transcriptions'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_data(self, input: OpenAIAudioTranscriptionsProcessorInput, configuration: OpenAIAudioTranscriptionsProcessorConfiguration) -> dict:
        return {
            'file': input.file.name,
            'model': configuration.model,
            'prompt': input.prompt,
            'response_format': configuration.response_format,
            'temperature': configuration.temperature,
            'language': input.language,
        }

    def _transform_api_response(self, input: OpenAIAudioTranscriptionsProcessorInput, configuration: OpenAIAudioTranscriptionsProcessorConfiguration, http_response: HttpAPIProcessorOutput) -> OpenAIAudioTranscriptionsProcessorOutput:
        return OpenAIAudioTranscriptionsProcessorOutput(
            text=json.loads(http_response.text)['text'],
            metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(http_response.text)),
        )

    def _process(self, input: OpenAIAudioTranscriptionsProcessorInput, configuration: OpenAIAPIProcessorConfiguration) -> BaseOutputType:
        """
            Invokes the API processor on the input and returns the output
        """
        http_api_processor = HttpAPIProcessor({'timeout': DEFAULT_TIMEOUT})

        files = []
        files.append(
            ('file', (input.file.name, input.file.content, 'application/octet-stream')),
        )
        input = HttpAPIProcessorInput(
            url=self._get_api_url(),
            method='POST',
            body=RawRequestBody(
                files=files,
                data=self._get_api_request_data(input=input, configuration=configuration),
            ),
            headers={},
            authorization=BearerTokenAuth(token=input.env.openai_api_key),
        )
        http_response = http_api_processor.process(input.dict())

        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            response = self._transform_api_response(
                input, configuration, http_response,
            )
            return response
        else:
            raise Exception(process_openai_error_response(http_response))


class OpenAIAudioTranslationsProcessorInput(OpenAIAPIProcessorInput):
    class Config:
        extra = Extra.forbid

    file: OpenAIFile = Field(
        ...,
        description='The audio file to translate, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.\n',
    )

    prompt: Optional[str] = Field(
        None,
        description="An optional text to guide the model's style or continue a previous audio segment. The [prompt](/docs/guides/speech-to-text/prompting) should be in English.\n",
    )


class OpenAIAudioTranslationsProcessorOutput(OpenAIAPIProcessorOutput):
    text: str


class OpenAIAudioTranslationsProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    model: str = Field(
        default='whisper-1',
        description='ID of the model to use. Only `whisper-1` is currently available.\n',
    )
    response_format: Optional[str] = Field(
        'json',
        description='The format of the transcript output, in one of these options: json, text, srt, verbose_json, or vtt.\n',
    )
    temperature: Optional[float] = Field(
        0,
        description='The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log_probability) to automatically increase the temperature until certain thresholds are hit.\n',
    )


class OpenAIAudioTranslationsProcessor(OpenAIAPIProcessor[OpenAIAudioTranslationsProcessorInput, OpenAIAudioTranslationsProcessorOutput, OpenAIAudioTranslationsProcessorConfiguration]):
    @ staticmethod
    def name() -> str:
        return 'openai_audio_translation_processor'

    def _get_api_url(self) -> str:
        return '{}/audio/translations'.format(OpenAIAPIProcessor.BASE_URL)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_data(self, input: OpenAIAudioTranslationsProcessorInput, configuration: OpenAIAudioTranslationsProcessorConfiguration) -> dict:
        return {
            'model': configuration.model,
            'file': input.file.name,
            'prompt': input.prompt,
            'response_format': configuration.response_format,
            'user': input.env.user,
        }

    def _transform_api_response(self, input: OpenAIAudioTranscriptionsProcessorInput, configuration: OpenAIAudioTranscriptionsProcessorConfiguration, http_response: HttpAPIProcessorOutput) -> OpenAIAudioTranscriptionsProcessorOutput:
        return OpenAIAudioTranslationsProcessorOutput(
            text=json.loads(http_response.text)['text'],
            metadata=OpenAIAPIProcessorOutputMetadata(raw_response=json.loads(http_response.text)),
        )

    def _process(self, input: OpenAIAPIProcessorInput, configuration: OpenAIAPIProcessorConfiguration) -> BaseOutputType:
        """
            Invokes the API processor on the input and returns the output
        """
        http_api_processor = HttpAPIProcessor({'timeout': DEFAULT_TIMEOUT})

        files = []
        files.append(
            ('file', (input.file.name, input.file.content, 'application/octet-stream')),
        )
        input = HttpAPIProcessorInput(
            url=self._get_api_url(),
            method='POST',
            body=RawRequestBody(
                files=files,
                data=self._get_api_request_data(input=input, configuration=configuration),
            ),
            headers={},
            authorization=BearerTokenAuth(token=input.env.openai_api_key),
        )
        http_response = http_api_processor.process(input.dict())

        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            response = self._transform_api_response(
                input, configuration, http_response,
            )
            return response
        else:
            raise Exception(process_openai_error_response(http_response))
