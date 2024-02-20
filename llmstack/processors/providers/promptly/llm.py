import logging
from enum import Enum
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.utils.sslr import LLM
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


class LLMProcessorConfiguration(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        description="The system message for the LLM", widget="textarea", advanced_parameter=False
    )
    provider: Provider = Field(
        default=Provider.OPENAI, description="The provider for the LLM", widget="select", advanced_parameter=False
    )
    model: Model = Field(
        default=Model.GPT_3_5_TURBO,
        description="The model for the LLM",
        widget="customselect",
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
        output_stream = self._output_stream
        google_api_key, token_type = get_google_credential_from_env(self._env)

        client = LLM(
            provider=self._config.provider,
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
            model=self._config.model,
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
