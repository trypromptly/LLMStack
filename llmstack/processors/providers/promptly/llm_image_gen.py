import logging
from enum import Enum
from typing import Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
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
    input_message: str = Field(description="The input message for the LLM", json_schema_extra={"widget": "textarea"})


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
    SD_3 = "sd3"
    SD_3_TURBO = "sd3-turbo"

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
        elif self.value == "sd3":
            return "sd3"
        elif self.value == "sd3-turbo":
            return "sd3-turbo"
        else:
            raise ValueError(f"Unknown model {self.value}")


class StabilityAIModelConfig(BaseModel):
    provider: Literal["stabilityai"] = "stabilityai"
    model: StabilityAIModel = Field(default=StabilityAIModel.STABLE_DIFFUSION, description="The model for the LLM")


class LLMImageGeneratorProcessorConfiguration(ApiProcessorSchema):
    provider_config: Union[OpenAIModelConfig, StabilityAIModelConfig] = Field(
        json_schema_extra={"advanced_parameter": False, "descrmination_field": "provider"}
    )

    seed: Optional[int] = Field(default=None, description="The seed used to generate the random number.")
    height: Optional[int] = Field(
        default=1024,
        description="The height of the image to generate.",
        le=2048,
        ge=0,
        json_schema_extra={"advanced_parameter": False},
    )
    width: Optional[int] = Field(
        default=1024,
        description="The width of the image to generate.",
        le=2048,
        ge=0,
        json_schema_extra={"advanced_parameter": False},
    )
    aspect_ratio: Optional[str] = Field(
        default="1:1",
        description="The aspect ratio of the image to generate.",
        json_schema_extra={"advanced_parameter": False},
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

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="""<pa-asset url="{{output_str}}" type="image/png"></pa-asset>""",
        )

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
        objref = self._upload_asset_from_url(asset=data_uri).objref
        async_to_sync(output_stream.write)(
            LLMImageGeneratorProcessorOutput(output_str=objref),
        )

        output = output_stream.finalize()
        return output
