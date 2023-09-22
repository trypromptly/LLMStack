from enum import Enum
from typing import Generator
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.blocks.llm.azure_openai import AzureOpenAIChatCompletionsAPIProcessor
from llmstack.common.blocks.llm.azure_openai import AzureOpenAIChatCompletionsAPIProcessorConfiguration
from llmstack.common.blocks.llm.azure_openai import AzureOpenAIChatCompletionsAPIProcessorInput
from llmstack.common.blocks.llm.azure_openai import AzureOpenAIChatCompletionsAPIProcessorOutput
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema, CHAT_WIDGET_NAME


class ChatCompletionsModel(str, Enum):
    GPT_4 = 'gpt-4'
    GPT_3_5 = 'gpt-35-turbo'
    GPT_3_5_16 = 'gpt-35-turbo-16k'
    GPT_4_32 = 'gpt-4-32k'

    def __str__(self):
        return self.value


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'

    def __str__(self):
        return self.value


class ChatMessage(ApiProcessorSchema):
    role: Optional[Role] = Field(
        default=Role.USER, description="The role of the message sender. Can be 'user' or 'assistant' or 'system'.",
    )
    content: Optional[str] = Field(default='', description='The message text.')


class AzureChatCompletionsInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default='', description='A message from the system, which will be prepended to the chat history.', widget='textarea',
    )
    chat_history: List[ChatMessage] = Field(
        default=[], description='A list of messages, each with a role and message text.', widget='hidden',
    )
    messages: List[ChatMessage] = Field(
        default=[ChatMessage()], description='A list of messages, each with a role and message text.',
    )


class AzureChatCompletionsOutput(ApiProcessorSchema):
    choices: List[ChatMessage] = Field(
        default=[], description='Messages', widget=CHAT_WIDGET_NAME,
    )
    _api_response: Optional[dict] = Field(
        default={}, description='Raw processor output.',
    )


def num_tokens_from_messages(messages, model='gpt-35-turbo'):
    import tiktoken
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding('cl100k_base')
    if model == 'gpt-35-turbo':
        return num_tokens_from_messages(messages, model='gpt-3.5-turbo-0301')
    elif model == 'gpt-4' or model == 'gpt-4-32k':
        return num_tokens_from_messages(messages, model='gpt-4-0314')
    elif model == 'gpt-35-turbo-0301':
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == 'gpt-4-0314':
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""",
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == 'name':
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


class AzureChatCompletionsConfiguration(AzureOpenAIChatCompletionsAPIProcessorConfiguration, ApiProcessorSchema):
    base_url: Optional[str] = Field(
        description='This value can be found in the Keys & Endpoint section when examining your resource from the Azure portal. An example endpoint is: https://docs-test-001.openai.azure.com/.',
    )

    deployment_name: ChatCompletionsModel = Field(
        description='This value will correspond to the custom name you chose for your deployment when you deployed a model. This value can be found under Resource Management > Deployments in the Azure portal or alternatively under Management > Deployments in Azure OpenAI Studio.',
        advanced_parameter=False, default=ChatCompletionsModel.GPT_4,
    )

    retain_history: Optional[bool] = Field(
        default=True, description='Retain and use the chat history. (Only works in apps)', advanced_parameter=False,
    )

    auto_prune_chat_history: Optional[bool] = Field(
        default=False, description="Automatically prune chat history. This is only applicable if 'retain_history' is set to 'true'.",
        hidden=True,
    )

    stream: Optional[bool] = Field(widget='hidden', default=True)


class AzureChatCompletions(ApiProcessorInterface[AzureChatCompletionsInput, AzureChatCompletionsOutput, AzureChatCompletionsConfiguration]):
    """
    Azure Chat Completions processor
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data['chat_history'] if 'chat_history' in session_data else [
        ]

    @staticmethod
    def name() -> str:
        return 'azure/chatgpt'

    @staticmethod
    def slug() -> str:
        return 'chatgpt'

    @staticmethod
    def provider_slug() -> str:
        return 'azure'

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history and self._config.auto_prune_chat_history:
            # Prune chat history
            while (num_tokens_from_messages(self._chat_history) > self._config.max_tokens) and len(self._chat_history) > 1:
                self._chat_history.pop(0)

            return {'chat_history': self._chat_history}

        return {'chat_history': self._chat_history}

    def process(self) -> dict:
        _env = self._env

        if self._config.stream != True:
            raise Exception(
                'Azure Chat Completions processor requires stream to be enabled.',
            )

        system_message = self._input.system_message
        if len(self._chat_history) == 0:
            # If we don't have any older chat history in the session, use the chat history from the input
            self._chat_history = self._input.chat_history
        chat_history = self._chat_history if self._config.retain_history else self._input.chat_history
        messages = self._input.messages

        azure_openai_api_key = _env.get('azure_openai_api_key')
        endpoint = self._config.base_url if self._config.base_url else _env.get(
            'azure_openai_endpoint', None,
        )

        processor = AzureOpenAIChatCompletionsAPIProcessor(
            configuration=AzureOpenAIChatCompletionsAPIProcessorConfiguration(
                base_url=f'https://{endpoint}.openai.azure.com',
                deployment_name=self._config.deployment_name,
                stream=self._config.stream,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            ).dict(),
        )

        result_iter: Generator[AzureOpenAIChatCompletionsAPIProcessorOutput] = processor.process_iter(
            AzureOpenAIChatCompletionsAPIProcessorInput(
                env={'azure_openai_api_key': azure_openai_api_key},
                system_message=system_message,
                chat_history=chat_history,
                messages=messages,
            ).dict(),
        )

        for result in result_iter:
            if result.choices[0].role == None and result.choices[0].content == None:
                continue
            async_to_sync(self._output_stream.write)(
                AzureChatCompletionsOutput(
                    choices=result.choices,
                ),
            )

        output = self._output_stream.finalize()

        # Update chat history
        for message in messages:
            self._chat_history.append(message)
        self._chat_history.append(
            {'role': 'assistant', 'content': output.choices[0].content},
        )

        return output
