import logging
from enum import Enum
from typing import Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.google import get_google_credential_from_env

logger = logging.getLogger(__name__)


class Model(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    GEMINI_PRO = "gemini-pro"
    CLAUDE_2_1 = "claude-2.1"

    def __str__(self):
        return self.value


class Provider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"

    def __str__(self):
        return self.value


class LLMProcessorInput(ApiProcessorSchema):
    input_message: str = Field(description="The input message for the LLM", widget="textarea")


class LLMProcessorOutput(ApiProcessorSchema):
    output_str: str = ""


class OpenAIModel(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"

    def __str__(self):
        return self.value


class OpenAIModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.GPT_3_5_TURBO, description="The model for the LLM")


class GoogleModel(str, Enum):
    GEMINI_PRO = "gemini-pro"

    def __str__(self):
        return self.value


class GoogleModelConfig(BaseModel):
    provider: Literal["google"] = "google"
    model: GoogleModel = Field(default=GoogleModel.GEMINI_PRO, description="The model for the LLM")


class AnthropicModel(str, Enum):
    CLAUDE_2_1 = "claude-2.1"

    def __str__(self):
        return self.value


class AnthropicModelConfig(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    model: AnthropicModel = Field(default=AnthropicModel.CLAUDE_2_1, description="The model for the LLM")


class LLMProcessorConfiguration(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        description="The system message for the LLM", widget="textarea", advanced_parameter=False
    )

    provider_config: Union[OpenAIModelConfig, GoogleModelConfig, AnthropicModelConfig] = Field(
        descrmination_field="provider",
        advanced_parameter=False,
    )

    max_tokens: Optional[int] = Field(
        default=100,
        description="The maximum number of tokens to generate before stopping.",
        le=8192,
        ge=0,
        advanced_parameter=False,
    )
    seed: Optional[int] = Field(
        default=None,
        description="The seed used to generate the random number.",
        advanced_parameter=True,
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="The temperature of the random number generator.",
        le=1.0,
        ge=0.0,
        advanced_parameter=False,
    )


class LLMProcessor(ApiProcessorInterface[LLMProcessorInput, LLMProcessorOutput, LLMProcessorConfiguration]):
    """
    Echo processor
    """

    @staticmethod
    def name() -> str:
        return "LLM"

    @staticmethod
    def slug() -> str:
        return "llm"

    @staticmethod
    def description() -> str:
        return "Simple LLM processor for all providers"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def process(self) -> dict:
        from llmstack.common.utils.sslr import LLM

        output_stream = self._output_stream
        google_api_key, token_type = get_google_credential_from_env(self._env)

        client = LLM(
            provider=self._config.provider_config.provider,
            openai_api_key=self._env.get("openai_api_key"),
            stabilityai_api_key=self._env.get("stabilityai_api_key"),
            google_api_key=google_api_key,
            anthropic_api_key=self._env.get("anthropic_api_key"),
        )

        messages = []
        if self._config.system_message:
            messages.append({"role": "system", "content": self._config.system_message})
        if self._input.input_message:
            messages.append({"role": "user", "content": self._input.input_message})

        result = client.chat.completions.create(
            messages=messages,
            model=self._config.provider_config.model.value,
            max_tokens=self._config.max_tokens,
            stream=True,
            seed=self._config.seed,
            temperature=self._config.temperature,
        )
        for entry in result:
            async_to_sync(output_stream.write)(
                LLMProcessorOutput(
                    output_str=entry.choices[0].delta.content_str,
                ),
            )
        output = output_stream.finalize()
        return output
