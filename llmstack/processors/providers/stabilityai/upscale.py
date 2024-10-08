import base64
import logging
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.common.utils.sslr.constants import PROVIDER_STABILITYAI
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class StabilityAIModel(StrEnum):
    ESRGAN_V1 = "esrgan-v1"

    def model_name(self):
        if self.value == "esrgan-v1":
            return "esrgan-v1-x2plus"
        else:
            raise ValueError(f"Unknown model {self.value}")


class UpscaleProcessorInput(ApiProcessorSchema):
    image_file: Optional[str] = Field(
        default="",
        description="The file to extract text from",
        json_schema_extra={
            "widget": "file",
            "accepts": {
                "image/jpeg": [],
                "image/png": [],
            },
            "maxSize": 9000000,
        },
    )
    image_file_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of file",
    )

    width: Optional[int] = Field(
        default=512,
        description="The width of the image.",
    )

    height: Optional[int] = Field(
        default=512,
        description="The height of the image.",
    )
    prompt: Optional[str] = Field(
        default=None,
        description="The prompt to use for processing.",
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="The negative prompt to use for processing.",
    )


class UpscaleProcessorOutput(ApiProcessorSchema):
    image: str = Field(
        default="",
        description="The generated images.",
    )


class UpscaleProcessorConfiguration(ApiProcessorSchema):
    engine_id: StabilityAIModel = Field(
        default=StabilityAIModel.ESRGAN_V1,
        description="The engine to use for processing.",
    )
    creativity: Optional[float] = Field(
        default=0.3, description="The creativity level to use for processing.", le=0.35, ge=0.0, multiple_of=0.01
    )
    seed: Optional[int] = Field(
        default=None,
        description="The seed to use for processing.",
    )


class UpscaleProcessor(
    ApiProcessorInterface[UpscaleProcessorInput, UpscaleProcessorOutput, UpscaleProcessorConfiguration]
):
    """
    StabilityAI Upscaler
    """

    @staticmethod
    def name() -> str:
        return "Image Upscaler"

    @staticmethod
    def slug() -> str:
        return "upscale"

    @staticmethod
    def description() -> str:
        return "Create a higher resolution version of an input image."

    @staticmethod
    def provider_slug() -> str:
        return "stabilityai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""![Generated Image]({{ image }})""",
            jsonpath="$.image",
        )

    def process(self) -> dict:
        from llmstack.common.utils.sslr import LLM
        from llmstack.common.utils.sslr._utils import resize_image_file

        image_file = self._input.image_file or None
        if (image_file is None or image_file == "") and self._input.image_file_data:
            image_file = self._input.image_file_data
        if image_file is None:
            raise Exception("No file found in input")

        # Extract from objref if it is one
        image_file = self._get_session_asset_data_uri(image_file)

        mime_type, file_name, data = validate_parse_data_uri(image_file)
        data_bytes = base64.b64decode(data)
        data_bytes = resize_image_file(data_bytes, max_pixels=9437184, max_size=10485760)

        provider_config = self.get_provider_config(model_slug=self._config.engine_id.model_name())
        client = LLM(provider=PROVIDER_STABILITYAI, stabilityai_api_key=provider_config.api_key)

        result = client.images.edit(
            prompt="Upscale" if self._input.prompt is None else self._input.prompt,
            image=data_bytes,
            model=self._config.engine_id.model_name(),
            n=1,
            response_format="b64_json",
            operation="upscale",
            size=f"{self._input.width}x{self._input.height}",
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        objref = self._upload_asset_from_url(asset=data_uri).objref
        async_to_sync(self._output_stream.write)(
            UpscaleProcessorOutput(image=objref),
        )
        output = self._output_stream.finalize()
        return output
