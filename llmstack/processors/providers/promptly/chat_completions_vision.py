import copy
import logging
from typing import Annotated, List, Literal, Optional, Union

import requests
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.anthropic.messages import (
    MessagesModel as AnthropicModel,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.google.chat import GeminiModel as GoogleModel
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.openai.chat_completions_vision import (
    ChatCompletionsVisionModel as OpenAIModel,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class TextMessage(BaseModel):
    type: Literal["text"] = "text"

    text: str = Field(
        default="",
        description="The message text.",
    )


class UrlImageMessage(BaseModel):
    type: Literal["image_url"] = "image_url"

    image_url: str = Field(
        default="",
        description="The image data URI.",
    )


Message = Annotated[
    Union[TextMessage, UrlImageMessage],
    Field(json_schema_extra={"descriminator": "type"}),
]


class LLMVisionProcessorInput(ApiProcessorSchema):
    messages: List[Message] = Field(
        default=[],
        description="A list of messages, each with a role and message text.",
    )


class LLMVisionProcessorOutput(ApiProcessorSchema):
    output_str: Optional[str] = Field(
        default=None, description="The output string from the LLM", json_schema_extra={"widget": "hidden"}
    )
    text: Optional[str] = Field(
        default=None, description="The output text from the LLM", json_schema_extra={"widget": "textarea"}
    )
    objref: Optional[str] = Field(
        default=None, description="The object reference for the output", json_schema_extra={"widget": "hidden"}
    )


class OpenAIVisionModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.GPT_4_O_MINI, description="The model for the LLM")


class GoogleVisionModelConfig(BaseModel):
    provider: Literal["google"] = "google"
    model: GoogleModel = Field(default=GoogleModel.GEMINI_1_5_PRO, description="The model for the LLM")


class AnthropicVisionModelConfig(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    model: AnthropicModel = Field(default=AnthropicModel.CLAUDE_3_Haiku, description="The model for the LLM")


ProviderConfigType = Union[GoogleVisionModelConfig, OpenAIVisionModelConfig, AnthropicVisionModelConfig]


class LLMVisionProcessorConfiguration(ApiProcessorSchema):
    provider_config: ProviderConfigType = Field(
        default=OpenAIVisionModelConfig(),
        json_schema_extra={"advanced_parameter": False, "descrmination_field": "provider"},
    )
    system_message: Optional[str] = Field(
        description="The system message for the LLM",
        default="You are a helpful assistant.",
        json_schema_extra={"widget": "textarea", "advanced_parameter": False},
    )

    max_tokens: Optional[int] = Field(
        default=100,
        description="The maximum number of tokens to generate before stopping.",
        le=8192,
        ge=0,
        json_schema_extra={"advanced_parameter": False},
    )
    seed: Optional[int] = Field(
        default=None,
        description="The seed used to generate the random number.",
        json_schema_extra={"advanced_parameter": True},
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="The temperature of the random number generator.",
        le=1.0,
        ge=0.0,
        json_schema_extra={"advanced_parameter": False},
    )
    objref: Optional[bool] = Field(
        default=False,
        title="Output as Object Reference",
        description="Return output as object reference instead of raw text.",
    )
    retain_history: Optional[bool] = Field(
        default=False,
        title="Retain History",
        description="Retain the history of the conversation.",
    )
    max_history: Optional[int] = Field(
        default=5,
        title="Max History",
        description="The maximum number of messages to retain in the history.",
        le=100,
        ge=0,
    )


class LLMVisionProcessor(
    ApiProcessorInterface[LLMVisionProcessorInput, LLMVisionProcessorOutput, LLMVisionProcessorConfiguration]
):
    """
    Simple LLM processor
    """

    @staticmethod
    def name() -> str:
        return "GPT Vision"

    @staticmethod
    def slug() -> str:
        return "llm_vision"

    @staticmethod
    def description() -> str:
        return "LLM Chat completions with Vision processor"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="""{{text}}""",
            jsonpath="$.text",
        )

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history}

    def process_session_data(self, session_data):
        self._chat_history = session_data.get("chat_history", [])

    def get_image_bytes_mime_type(self, image_url: str):
        response = requests.get(image_url)
        if response.status_code != 200:
            raise ValueError(f"Invalid image URL: {image_url}")
        image_bytes = response.content
        mime_type = response.headers["Content-Type"]
        return image_bytes, mime_type

    def process(self) -> dict:
        messages = self._chat_history if self._config.retain_history else []
        input_tokens = None
        output_tokens = None

        if self._input.messages:
            parts = []
            for input_message in self._input.messages:
                if isinstance(input_message, TextMessage):
                    parts.append(
                        {
                            "mime_type": "text/plain",
                            "type": "text",
                            "data": input_message.text,
                        }
                    )
                elif isinstance(input_message, UrlImageMessage):
                    image_url = input_message.image_url
                    content = None
                    mime_type = None
                    if image_url.startswith("data:"):
                        content, mime_type = image_url.split(",", 1)
                    elif image_url.startswith("http"):
                        content, mime_type = self.get_image_bytes_mime_type(image_url)
                    elif image_url.startswith("objref://"):
                        data_uri = self._get_session_asset_data_uri(image_url, include_name=True)
                        mime_type, _, content = validate_parse_data_uri(data_uri)

                    if mime_type and content:
                        parts.append(
                            {
                                "type": "blob",
                                "data": content,
                                "mime_type": mime_type,
                            }
                        )

            messages.append(
                {
                    "role": "user",
                    "content": parts,
                }
            )

        client = get_llm_client_from_provider_config(
            provider=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.value,
            get_provider_config_fn=self.get_provider_config,
        )
        provider_config = self.get_provider_config(
            provider_slug=self._config.provider_config.provider, model_slug=self._config.provider_config.model.value
        )

        messages_to_send = (
            [{"role": "system", "content": self._config.system_message}] + messages
            if self._config.system_message
            else messages
        )
        response = client.chat.completions.create(
            messages=messages_to_send,
            model=self._config.provider_config.model.model_name(),
            stream=True,
            n=1,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
        )

        for result in response:
            if result.usage:
                input_tokens = result.usage.input_tokens
                output_tokens = result.usage.output_tokens

            choice = result.choices[0]
            if choice.delta.content:
                async_to_sync(self._output_stream.write)(LLMVisionProcessorOutput(text=choice.delta.content_str))

        if input_tokens:
            self._usage_data.append(
                (
                    f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                    MetricType.INPUT_TOKENS,
                    (provider_config.provider_config_source, input_tokens),
                )
            )
        if output_tokens:
            self._usage_data.append(
                (
                    f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                    MetricType.OUTPUT_TOKENS,
                    (provider_config.provider_config_source, output_tokens),
                )
            )
        output = self._output_stream.finalize()

        if self._config.retain_history:
            self._chat_history = copy.deepcopy(messages)
            self._chat_history.append({"role": "assistant", "content": output.text})

        return output
