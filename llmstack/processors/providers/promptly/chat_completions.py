import logging
import uuid
from typing import Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.anthropic.messages import (
    MessagesModel as AnthropicModel,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.cohere.chat import CohereModel
from llmstack.processors.providers.google.chat import GeminiModel as GoogleModel
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.mistral.chat_completions import (
    MessagesModel as MistralModel,
)
from llmstack.processors.providers.openai.chat_completions import (
    ChatCompletionsModel as OpenAIModel,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class LLMProcessorInput(ApiProcessorSchema):
    input_message: str = Field(
        description="The input message for the LLM", json_schema_extra={"widget": "textarea"}, default=""
    )


class LLMProcessorOutput(ApiProcessorSchema):
    output_str: Optional[str] = Field(
        default=None, description="The output string from the LLM", json_schema_extra={"widget": "hidden"}
    )
    text: Optional[str] = Field(
        default=None, description="The output text from the LLM", json_schema_extra={"widget": "textarea"}
    )
    objref: Optional[str] = Field(
        default=None, description="The object reference for the output", json_schema_extra={"widget": "hidden"}
    )


class OpenAIModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.GPT_4_O_MINI, description="The model for the LLM")


class GoogleModelConfig(BaseModel):
    provider: Literal["google"] = "google"
    model: GoogleModel = Field(default=GoogleModel.GEMINI_1_5_FLASH, description="The model for the LLM")


class AnthropicModelConfig(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    model: AnthropicModel = Field(default=AnthropicModel.CLAUDE_3_Haiku, description="The model for the LLM")


class CohereModelConfig(BaseModel):
    provider: Literal["cohere"] = "cohere"
    model: CohereModel = Field(default=CohereModel.COMMAND, description="The model for the LLM")


class MistralModelConfig(BaseModel):
    provider: Literal["mistral"] = "mistral"
    model: MistralModel = Field(default=MistralModel.MIXTRAL_SMALL, description="The model for the LLM")


ProviderConfigType = Union[
    OpenAIModelConfig, GoogleModelConfig, AnthropicModelConfig, CohereModelConfig, MistralModelConfig
]


class LLMProcessorConfiguration(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        description="The system message for the LLM",
        default="You are a helpful assistant.",
        json_schema_extra={"widget": "textarea", "advanced_parameter": False},
    )

    provider_config: Union[
        OpenAIModelConfig, GoogleModelConfig, AnthropicModelConfig, CohereModelConfig, MistralModelConfig
    ] = Field(
        default=OpenAIModelConfig(), json_schema_extra={"advanced_parameter": False, "descrmination_field": "provider"}
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


class LLMProcessor(ApiProcessorInterface[LLMProcessorInput, LLMProcessorOutput, LLMProcessorConfiguration]):
    """
    Simple LLM processor
    """

    @staticmethod
    def name() -> str:
        return "Chat Completions"

    @staticmethod
    def slug() -> str:
        return "llm"

    @staticmethod
    def description() -> str:
        return "LLM Chat completions processor"

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

    def process(self) -> dict:
        input_tokens = None
        output_tokens = None

        output_stream = self._output_stream
        client = get_llm_client_from_provider_config(
            provider=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.value,
            get_provider_config_fn=self.get_provider_config,
        )
        provider_config = self.get_provider_config(
            provider_slug=self._config.provider_config.provider, model_slug=self._config.provider_config.model.value
        )

        messages = []
        if self._config.system_message:
            messages.append({"role": "system", "content": self._config.system_message})

        if self._config.retain_history:
            if self._config.max_history:
                self._chat_history = self._chat_history[-self._config.max_history :]
            messages.extend(self._chat_history)

        if self._input.input_message:
            messages.append({"role": "user", "content": self._input.input_message})

        result = client.chat.completions.create(
            messages=messages,
            model=self._config.provider_config.model.model_name(),
            max_tokens=self._config.max_tokens,
            stream=True,
            seed=self._config.seed,
            temperature=self._config.temperature,
        )

        # Stream output to asset_stream if objref is enabled
        asset_stream = None
        if self._config.objref:
            asset_stream = self._create_asset_stream(mime_type="text/plain", file_name=str(uuid.uuid4()) + ".txt")
            async_to_sync(output_stream.write)(
                LLMProcessorOutput(
                    objref=asset_stream.objref,
                ),
            )

        for entry in result:
            if entry.usage:
                input_tokens = entry.usage.input_tokens
                output_tokens = entry.usage.output_tokens

            # Stream the output if objref is not enabled
            if not self._config.objref:
                async_to_sync(output_stream.write)(
                    LLMProcessorOutput(
                        output_str=entry.choices[0].delta.content_str,
                        text=entry.choices[0].delta.content_str,
                    ),
                )
            elif asset_stream:
                try:
                    asset_stream.append_chunk(str.encode(entry.choices[0].delta.content_str))
                except Exception as e:
                    logger.error(f"Error streaming output: {e}")
                    break

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
        if asset_stream:
            asset_stream.finalize()

        output = output_stream.finalize()

        if self._config.retain_history:
            self._chat_history.extend(
                [{"role": "user", "content": self._input.input_message}, {"role": "assistant", "content": output.text}]
            )

        return output
