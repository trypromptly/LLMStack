import logging
from typing import Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.openai.images_generations import (
    ImageModel as OpenAIModel,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config
from llmstack.processors.providers.stabilityai.text_to_image import StabilityAIModel

logger = logging.getLogger(__name__)


class Provider(StrEnum):
    OPENAI = "openai"
    GOOGLE = "google"
    STABILITYAI = "stabilityai"


class LLMImageGeneratorProcessorInput(ApiProcessorSchema):
    input_message: str = Field(description="The input message for the LLM", json_schema_extra={"widget": "textarea"})


class LLMImageGeneratorProcessorOutput(ApiProcessorSchema):
    output_str: str = ""


class OpenAIModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.DALL_E_2, description="The model for the LLM")


class StabilityAIModelConfig(BaseModel):
    provider: Literal["stabilityai"] = "stabilityai"
    model: StabilityAIModel = Field(default=StabilityAIModel.SD_3_MEDIUM, description="The model for the LLM")


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
        output_stream = self._output_stream

        client = get_llm_client_from_provider_config(
            provider=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.model_name(),
            get_provider_config_fn=self.get_provider_config,
        )
        provider_config = self.get_provider_config(
            provider_slug=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.model_name(),
        )
        size = f"{self._config.width}x{self._config.height}"

        result = client.images.generate(
            prompt=self._input.input_message,
            model=self._config.provider_config.model.model_name(),
            n=1,
            response_format="b64_json",
            size=size,
        )
        self._usage_data.append(
            (
                f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                MetricType.RESOLUTION,
                (provider_config.provider_config_source, size, "hd"),
            )
        )
        self._usage_data.append(
            (
                f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                MetricType.API_INVOCATION,
                (provider_config.provider_config_source, 1),
            )
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        objref = self._upload_asset_from_url(asset=data_uri).objref
        async_to_sync(output_stream.write)(
            LLMImageGeneratorProcessorOutput(output_str=objref),
        )

        output = output_stream.finalize()
        return output
