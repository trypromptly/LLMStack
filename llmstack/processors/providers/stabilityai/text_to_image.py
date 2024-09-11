import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType

logger = logging.getLogger(__name__)


class StabilityAIModel(StrEnum):
    CORE = "core"
    SD_3 = "sd3"
    SD_3_TURBO = "sd3-large-turbo"
    SD_3_LARGE = "sd3-large"
    SD_3_MEDIUM = "sd3-medium"
    ULTRA = "ultra"

    def model_name(self):
        return self.value


class TextToImageInput(ApiProcessorSchema):
    prompt: List[str] = Field(
        default=[""],
        description="Text prompt to use for image generation.",
    )

    negative_prompt: List[str] = Field(
        default=[""],
        description="Negative text prompt to use for image generation.",
    )


class TextToImageOutput(ApiProcessorSchema):
    answer: Optional[str] = Field(default=None, description="The generated images.")


class TextToImageConfiguration(ApiProcessorSchema):
    engine_id: StabilityAIModel = Field(
        default=StabilityAIModel.SD_3_MEDIUM,
        description="Inference engine (model) to use.",
        json_schema_extra={"advanced_parameter": False},
    )
    height: Optional[int] = Field(
        default=512,
        description="Measured in pixels. Pixel limit is 1048576",
    )
    width: Optional[int] = Field(
        default=512,
        description="Measured in pixels. Pixel limit is 1048576.",
    )
    seed: Optional[int] = Field(
        default=0,
        description="Seed for random latent noise generation. Deterministic if not being used in concert with CLIP Guidance. If not specified, or set to 0, then a random value will be used.",
        json_schema_extra={"advanced_parameter": False},
    )


class TextToImage(ApiProcessorInterface[TextToImageInput, TextToImageOutput, TextToImageConfiguration]):
    """
    StabilityAI Images Generations API
    """

    @staticmethod
    def name() -> str:
        return "Text2Image"

    @staticmethod
    def slug() -> str:
        return "text2image"

    @staticmethod
    def description() -> str:
        return "Generates images from a series of prompts and negative prompts"

    @staticmethod
    def provider_slug() -> str:
        return "stabilityai"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""<pa-asset url="{{answer}}" type="image/*"></pa-asset>""",
        )

    def process(self) -> dict:
        from llmstack.common.utils.sslr import LLM

        provider_config = self.get_provider_config(model_slug=self._config.engine_id.model_name())
        client = LLM(
            provider="stabilityai",
            stabilityai_api_key=provider_config.api_key,
        )
        result = client.images.generate(
            prompt=" ".join(self._input.prompt),
            negative_prompt=" ".join(self._input.negative_prompt) if self._input.negative_prompt else None,
            model=self._config.engine_id.model_name(),
            n=1,
            response_format="b64_json",
            size=f"{self._config.width}x{self._config.height}",
        )
        self._usage_data.append(
            (
                f"{self.provider_slug()}/*/{self._config.engine_id.value}/*",
                MetricType.API_INVOCATION,
                (provider_config.provider_config_source, 1),
            )
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        objref = self._upload_asset_from_url(asset=data_uri).objref
        async_to_sync(self._output_stream.write)(TextToImageOutput(answer=objref))
        output = self._output_stream.finalize()
        return output
