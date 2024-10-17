import copy
import logging
from typing import Annotated, List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field, confloat, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.common.blocks.llm.openai import (
    OpenAIChatCompletionsAPIProcessorConfiguration,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatCompletionsVisionModel(StrEnum):
    GPT_4_Vision = "gpt-4-vision-preview"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_TURBO_240409 = "gpt-4-turbo-2024-04-09"
    GPT_4_1106_VISION_PREVIEW = "gpt-4-1106-vision-preview"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    O1_PREVIEW = "o1-preview"
    O1_MINI = "o1-mini"

    def model_name(self):
        return self.value


class TextMessage(BaseModel):
    type: Literal["text"]

    text: str = Field(
        default="",
        description="The message text.",
    )


class UrlImageMessage(BaseModel):
    type: Literal["image_url"]

    image_url: str = Field(
        default="",
        description="The image data URI.",
    )


Message = Annotated[
    Union[TextMessage, UrlImageMessage],
    Field(json_schema_extra={"descriminator": "type"}),
]


class ChatMessage(ApiProcessorSchema):
    role: Optional[Role] = Field(
        default=Role.USER,
        description="The role of the message sender. Can be 'user' or 'assistant' or 'system'.",
    )
    content: List[Union[TextMessage, UrlImageMessage]] = Field(
        default=[],
        description="The message text.",
    )


class ChatCompletionsVisionInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default="",
        description="A message from the system, which will be prepended to the chat history.",
        json_schema_extra={"widget": "textarea"},
    )
    messages: List[Message] = Field(
        default=[],
        description="A list of messages, each with a role and message text.",
    )


class ChatCompletionsVisionOutput(ApiProcessorSchema):
    result: str = Field(default="", description="The model-generated message.")


class ChatCompletionsVisionConfiguration(
    OpenAIChatCompletionsAPIProcessorConfiguration,
    ApiProcessorSchema,
):
    model: ChatCompletionsVisionModel = Field(
        default=ChatCompletionsVisionModel.GPT_4_Vision,
        description="ID of the model to use. Currently, only `gpt-4-vision-preview` is supported.",
        json_schema_extra={"advanced_parameter": False},
    )
    max_tokens: Optional[conint(ge=1, le=32000)] = Field(
        1024,
        description="The maximum number of tokens allowed for the generated answer. By default, the number of tokens the model can return will be (4096 - prompt tokens).\n",
        json_schema_extra={"advanced_parameter": False, "example": 1024},
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n",
        json_schema_extra={"advanced_parameter": False, "example": 1},
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
        json_schema_extra={"advanced_parameter": False},
    )

    auto_prune_chat_history: Optional[bool] = Field(
        default=False,
        description="Automatically prune chat history. This is only applicable if 'retain_history' is set to 'true'.",
    )


class ChatCompletionsVision(
    ApiProcessorInterface[ChatCompletionsVisionInput, ChatCompletionsVisionOutput, ChatCompletionsVisionConfiguration],
):
    """
    OpenAI Chat Completions with vision API
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    @staticmethod
    def name() -> str:
        return "ChatGPT with Vision"

    @staticmethod
    def slug() -> str:
        return "chatgpt_vision"

    @staticmethod
    def description() -> str:
        return "Takes a series of messages as input, and return a model-generated message as output"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{result}}""",
            jsonpath="$.result",
        )

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history}

    def process(self) -> dict:
        messages = self._chat_history if self._config.retain_history else []

        if self._input.messages:
            user_message_content = []
            for input_message in self._input.messages:
                if isinstance(input_message, TextMessage):
                    user_message_content.append(
                        {
                            "type": "text",
                            "text": input_message.text,
                        }
                    )
                elif isinstance(input_message, UrlImageMessage):
                    image_url = input_message.image_url
                    data_uri = None
                    if image_url.startswith("data:") or image_url.startswith("http"):
                        data_uri = image_url
                    elif image_url.startswith("objref://"):
                        data_uri = self._get_session_asset_data_uri(image_url, include_name=False)

                    if data_uri:
                        user_message_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_uri,
                                },
                            }
                        )

            messages.append(
                {
                    "role": "user",
                    "content": user_message_content,
                }
            )

        client = get_llm_client_from_provider_config("openai", self._config.model, self.get_provider_config)
        provider_config = self.get_provider_config(provider_slug="openai", model_slug=self._config.model)
        messages_to_send = (
            [{"role": "system", "content": self._input.system_message}] + messages
            if self._input.system_message
            else messages
        )

        response = client.chat.completions.create(
            messages=messages_to_send,
            model=self._config.model,
            stream=True,
            n=1,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
        )

        for result in response:
            if result.usage:
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                        MetricType.INPUT_TOKENS,
                        (provider_config.provider_config_source, result.usage.input_tokens),
                    )
                )
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                        MetricType.OUTPUT_TOKENS,
                        (provider_config.provider_config_source, result.usage.output_tokens),
                    )
                )

            choice = result.choices[0]
            if choice.delta.content:
                async_to_sync(self._output_stream.write)(ChatCompletionsVisionOutput(result=choice.delta.content))

        output = self._output_stream.finalize()
        if self._config.retain_history:
            self._chat_history = copy.deepcopy(messages)
            self._chat_history.append({"role": "assistant", "content": output.result})
        return output
