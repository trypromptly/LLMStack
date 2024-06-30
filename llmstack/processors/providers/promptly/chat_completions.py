import logging
import uuid
from enum import Enum
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
from llmstack.processors.providers.google import get_google_credential_from_env
from llmstack.processors.providers.mistral.chat_completions import (
    MessagesModel as MistralModel,
)

logger = logging.getLogger(__name__)


class Model(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_O = "gpt-4o"
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
    input_message: str = Field(
        description="The input message for the LLM", json_schema_extra={"widget": "textarea"}, default=""
    )


class LLMProcessorOutput(ApiProcessorSchema):
    output_str: Optional[str] = Field(description="The output string from the LLM", widget="hidden")
    text: Optional[str] = Field(description="The output text from the LLM", widget="textarea")
    objref: Optional[str] = Field(description="The object reference for the output", widget="hidden")


class OpenAIModel(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    GPT_4_O = "gpt-4o"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class OpenAIModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.GPT_3_5_TURBO, description="The model for the LLM")


class GoogleModel(str, Enum):
    GEMINI_PRO = "gemini-pro"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class GoogleModelConfig(BaseModel):
    provider: Literal["google"] = "google"
    model: GoogleModel = Field(default=GoogleModel.GEMINI_PRO, description="The model for the LLM")


class AnthropicModelConfig(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    model: AnthropicModel = Field(default=AnthropicModel.CLAUDE_3_Haiku, description="The model for the LLM")


class CohereModel(str, Enum):
    COMMAND = "command"
    COMMAND_LIGHT = "command-light"
    COMMAND_NIGHTLY = "command-nightly"
    COMMAND_LIGHT_NIGHTLY = "command-light-nightly"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class CohereModelConfig(BaseModel):
    provider: Literal["cohere"] = "cohere"
    model: CohereModel = Field(default=CohereModel.COMMAND, description="The model for the LLM")


class MistralModelConfig(BaseModel):
    provider: Literal["mistral"] = "mistral"
    model: MistralModel = Field(default=MistralModel.MIXTRAL_SMALL, description="The model for the LLM")


class LLMProcessorConfiguration(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        description="The system message for the LLM", json_schema_extra={"widget": "textarea"}, advanced_parameter=False
    )

    provider_config: Union[
        OpenAIModelConfig, GoogleModelConfig, AnthropicModelConfig, CohereModelConfig, MistralModelConfig
    ] = Field(
        descrmination_field="provider",
        json_schema_extra={"advanced_parameter": False},
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
        advanced_parameter=True,
    )
    retain_history: Optional[bool] = Field(
        default=False,
        title="Retain History",
        description="Retain the history of the conversation.",
        advanced_parameter=True,
    )
    max_history: Optional[int] = Field(
        default=5,
        title="Max History",
        description="The maximum number of messages to retain in the history.",
        le=100,
        ge=0,
        advanced_parameter=True,
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
        )

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history}

    def process_session_data(self, session_data):
        self._chat_history = session_data.get("chat_history", [])

    def process(self) -> dict:
        from llmstack.common.utils.sslr import LLM

        output_stream = self._output_stream
        google_api_key, token_type = (
            get_google_credential_from_env(self._env) if self._env.get("google_service_account_json_key") else None
        )

        client = LLM(
            provider=self._config.provider_config.provider,
            openai_api_key=self._env.get("openai_api_key"),
            stabilityai_api_key=self._env.get("stabilityai_api_key"),
            google_api_key=google_api_key,
            anthropic_api_key=self._env.get("anthropic_api_key"),
            cohere_api_key=self._env.get("cohere_api_key"),
            mistral_api_key=self._env.get("mistral_api_key"),
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

        if asset_stream:
            asset_stream.finalize()

        output = output_stream.finalize()

        if self._config.retain_history:
            self._chat_history.extend(
                [{"role": "user", "content": self._input.input_message}, {"role": "assistant", "content": output.text}]
            )

        return output
