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


class Provider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    STABILITYAI = "stabilityai"

    def __str__(self):
        return self.value


class LLMImageGeneratorProcessorInput(ApiProcessorSchema):
    input_message: str = Field(description="The input message for the LLM", widget="textarea")


class LLMImageGeneratorProcessorOutput(ApiProcessorSchema):
    output_str: str = ""


class OpenAIModel(str, Enum):
    DALLE_2 = "dall-e-2"
    DALLE_3 = "dall-e-3"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class OpenAIModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.DALLE_3, description="The model for the LLM")


class StabilityAIModel(str, Enum):
    STABLE_DIFFUSION_XL = "stable-diffusion-xl"
    STABLE_DIFFUSION = "stable-diffusion"
    STABLE_DIFFUSION_XL_BETA = "stable-diffusion-xl-beta"
    CORE = "core"

    def __str__(self) -> str:
        return self.value

    def model_name(self):
        if self.value == "stable-diffusion-xl":
            return "stable-diffusion-xl-1024-v1-0"
        elif self.value == "stable-diffusion":
            return "stable-diffusion-v1-6"
        elif self.value == "stable-diffusion-xl-beta":
            return "stable-diffusion-xl-beta-v2-2-2"
        elif self.value == "core":
            return "core"
        else:
            raise ValueError(f"Unknown model {self.value}")


class StabilityAIModelConfig(BaseModel):
    provider: Literal["stabilityai"] = "stabilityai"
    model: StabilityAIModel = Field(default=StabilityAIModel.STABLE_DIFFUSION, description="The model for the LLM")


class LLMImageGeneratorProcessorConfiguration(ApiProcessorSchema):
    provider_config: Union[OpenAIModelConfig, StabilityAIModelConfig] = Field(
        descrmination_field="provider",
        advanced_parameter=False,
    )

    seed: Optional[int] = Field(
        default=None,
        description="The seed used to generate the random number.",
        advanced_parameter=True,
    )
    height: Optional[int] = Field(
        default=1024,
        description="The height of the image to generate.",
        le=2048,
        ge=0,
        advanced_parameter=False,
    )
    width: Optional[int] = Field(
        default=1024,
        description="The width of the image to generate.",
        le=2048,
        ge=0,
        advanced_parameter=False,
    )
    aspect_ratio: Optional[str] = Field(
        default="1:1",
        description="The aspect ratio of the image to generate.",
        advanced_parameter=False,
    )


class LLMImageGeneratorProcessor(
    ApiProcessorInterface[
        LLMImageGeneratorProcessorInput, LLMImageGeneratorProcessorOutput, LLMImageGeneratorProcessorConfiguration
    ]
):
    """
    Simple LLM processor
    """

    @staticmethod
    def name() -> str:
        return "Image Generator"

    @staticmethod
    def slug() -> str:
        return "image_generator"

    @staticmethod
    def description() -> str:
        return "Image Generator processor for all providers"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

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
        )

        result = client.images.generate(
            prompt=self._input.input_message,
            model=self._config.provider_config.model.model_name(),
            n=1,
            response_format="b64_json",
            size=f"{self._config.width}x{self._config.height}",
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        object_ref = self._upload_asset_from_url(asset=data_uri)
        async_to_sync(output_stream.write)(
            LLMImageGeneratorProcessorOutput(output_str=object_ref),
        )

        output = output_stream.finalize()
        return output
