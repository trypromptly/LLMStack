import base64
import logging
from enum import Enum
from io import BytesIO
from typing import Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.common.utils.sslr._utils import resize_image_file
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


class ImageEditOperation(str, Enum):
    UPSCALE = "upscale"
    VARIATION = "variation"
    SEARCH_REPLACE = "search_replace"
    REMOVE_BACKGROUND = "remove_background"

    def __str__(self):
        return self.value


class LLMImageEditProcessorInput(ApiProcessorSchema):
    input_image: str = Field(description="The input image for the LLM", widget="file")
    mask_image: Optional[str] = Field(
        default=None,
        description="The mask image for the LLM",
        widget="file",
        advanced_parameter=True,
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Prompt for the LLM",
        widget="textarea",
        advanced_parameter=True,
    )
    search_prompt: Optional[str] = Field(
        default=None,
        description="Search prompt for the LLM",
        widget="textarea",
        advanced_parameter=True,
    )
    operation: Optional[ImageEditOperation] = Field(
        default=ImageEditOperation.SEARCH_REPLACE,
        description="The operation to perform on the image",
    )


class LLMImageEditProcessorOutput(ApiProcessorSchema):
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


class LLMImageEditProcessorConfiguration(ApiProcessorSchema):
    provider_config: Union[OpenAIModelConfig, StabilityAIModelConfig] = Field(
        descrmination_field="provider",
        advanced_parameter=False,
    )

    seed: Optional[int] = Field(
        default=None,
        description="The seed used to generate the random number.",
        advanced_parameter=True,
    )


class LLMImageEditProcessor(
    ApiProcessorInterface[LLMImageEditProcessorInput, LLMImageEditProcessorOutput, LLMImageEditProcessorConfiguration]
):
    """
    Simple LLM processor
    """

    @staticmethod
    def name() -> str:
        return "Image Edit"

    @staticmethod
    def slug() -> str:
        return "image_edit"

    @staticmethod
    def description() -> str:
        return "Image Editor processor for all providers"

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

        input_img = self._input.input_image
        # If img is a data uri
        if input_img.startswith("data:image"):
            input_img = base64.b64decode(input_img.split(",")[1])

        # Max pixels = 4,194,304 and max size = 10MiB
        input_img = resize_image_file(input_img, 4194304, 10485760)

        extra_body = {}
        if self._input.search_prompt:
            extra_body["search_prompt"] = self._input.search_prompt

        logger.info(f"Operation: {self._input.operation}")
        result = client.images.edit(
            image=BytesIO(input_img),
            model=str(self._config.provider_config.model.model_name()),
            operation=str(self._input.operation),
            extra_body=extra_body,
            prompt=self._input.prompt,
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        object_ref = self._upload_asset_from_url(asset=data_uri)
        async_to_sync(output_stream.write)(
            LLMImageEditProcessorOutput(output_str=object_ref),
        )

        output = output_stream.finalize()
        return output
