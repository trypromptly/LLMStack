from typing import List, Optional

import openai
from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    CHAT_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)


class ChatCompletionsModel(StrEnum):
    GPT_4 = "gpt-4"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5 = "gpt-35-turbo"
    GPT_3_5_16 = "gpt-35-turbo-16k"
    GPT_4_32 = "gpt-4-32k"


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(ApiProcessorSchema):
    role: Optional[Role] = Field(
        default=Role.USER,
        description="The role of the message sender. Can be 'user' or 'assistant' or 'system'.",
    )
    content: Optional[str] = Field(default="", description="The message text.")


class AzureChatCompletionsInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default="",
        description="A message from the system, which will be prepended to the chat history.",
        json_schema_extra={"widget": "textarea"},
    )
    chat_history: List[ChatMessage] = Field(
        default=[],
        description="A list of messages, each with a role and message text.",
        json_schema_extra={"widget": "hidden"},
    )
    messages: List[ChatMessage] = Field(
        default=[
            ChatMessage(),
        ],
        description="A list of messages, each with a role and message text.",
    )


class AzureChatCompletionsOutput(ApiProcessorSchema):
    choices: List[ChatMessage] = Field(
        default=[],
        description="Messages",
        json_schema_extra={"widget": CHAT_WIDGET_NAME},
    )


def num_tokens_from_messages(messages, model="gpt-35-turbo"):
    import tiktoken

    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-35-turbo":
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4" or model == "gpt-4-32k":
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-35-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
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
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


class AzureChatCompletionsConfiguration(ApiProcessorSchema):
    temperature: Optional[float] = Field(
        le=2.0,
        ge=0.0,
        default=0.7,
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.",
    )
    top_p: Optional[float] = Field(
        description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.",
        default=1.0,
        ge=0.0,
        le=1.0,
    )
    max_tokens: Optional[int] = Field(
        description="The maximum number of tokens to generate.",
        ge=1,
        default=1024,
        le=32000,
    )
    base_url: Optional[str] = Field(
        default=None,
        description="This value can be found in the Keys & Endpoint section when examining your resource from the Azure portal. An example endpoint is: https://docs-test-001.openai.azure.com/.",
        json_schema_extra={"advanced_parameter": False},
    )
    api_version: Optional[str] = Field(
        description="The API version to use",
        default="2023-05-15",
    )
    deployment_name: str = Field(
        description="This value will correspond to the custom name you chose for your deployment when you deployed a model. This value can be found under Resource Management > Deployments in the Azure portal or alternatively under Management > Deployments in Azure OpenAI Studio.",
        json_schema_extra={
            "advanced_parameter": False,
            "widget": "customselect",
            "options": [x.value for x in ChatCompletionsModel],
        },
        default=ChatCompletionsModel.GPT_4,
    )
    retain_history: Optional[bool] = Field(
        default=True,
        description="Retain and use the chat history. (Only works in apps)",
        json_schema_extra={"advanced_parameter": False},
    )
    auto_prune_chat_history: Optional[bool] = Field(
        default=False,
        description="Automatically prune chat history. This is only applicable if 'retain_history' is set to 'true'.",
    )
    stream: Optional[bool] = Field(default=True, json_schema_extra={"widget": "hidden"})


class AzureChatCompletions(
    ApiProcessorInterface[AzureChatCompletionsInput, AzureChatCompletionsOutput, AzureChatCompletionsConfiguration],
):
    """
    Azure Chat Completions processor
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    @staticmethod
    def name() -> str:
        return "ChatGPT"

    @staticmethod
    def slug() -> str:
        return "chatgpt"

    @staticmethod
    def description() -> str:
        return "Chat completions from Azure Open AI"

    @staticmethod
    def provider_slug() -> str:
        return "azure"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{% for choice in choices %}
{{choice.content}}
{% endfor %}""",
            jsonpath="$.choices[0].content",
        )

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history and self._config.auto_prune_chat_history:
            # Prune chat history
            while (
                num_tokens_from_messages(
                    self._chat_history,
                )
                > self._config.max_tokens
            ) and len(
                self._chat_history,
            ) > 1:
                self._chat_history.pop(0)

            return {"chat_history": self._chat_history}

        if self._config.retain_history:
            return {"chat_history": self._chat_history}

        return {"chat_history": []}

    def process(self) -> dict:
        output_stream = self._output_stream

        if not self._config.stream:
            raise Exception(
                "Azure Chat Completions processor requires stream to be enabled.",
            )

        chat_history = self._chat_history if self._config.retain_history else []
        azure_provider_config = self.get_provider_config(model_slug=self._config.deployment_name)
        endpoint = self._config.base_url if self._config.base_url else azure_provider_config.azure_endpoint

        client = openai.AzureOpenAI(
            azure_endpoint=endpoint if endpoint.startswith("https://") else f"https://{endpoint}.openai.azure.com",
            api_key=azure_provider_config.api_key,
            api_version=self._config.api_version,
        )

        messages = []
        messages.append(
            {"role": "system", "content": self._input.system_message},
        )

        if len(chat_history) > 0:
            for message in chat_history:
                messages.append(message)

        for message in self._input.messages:
            messages.append(message.model_dump())

        result_iter = client.chat.completions.create(
            messages=messages,
            model=self._config.deployment_name,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            stream=True,
        )

        for data in result_iter:
            if (
                data.object == "chat.completion.chunk"
                and len(
                    data.choices,
                )
                > 0
                and data.choices[0].delta
                and data.choices[0].delta.content
            ):
                async_to_sync(
                    output_stream.write,
                )(
                    AzureChatCompletionsOutput(
                        choices=list(
                            map(
                                lambda entry: ChatMessage(
                                    role=entry.delta.role,
                                    content=entry.delta.content,
                                ),
                                data.choices,
                            ),
                        ),
                    ),
                )
        output = self._output_stream.finalize()

        # Update chat history
        for message in messages:
            self._chat_history.append(message)

        self._chat_history.append(
            {"role": "assistant", "content": output.choices[0].content},
        )
        return output
