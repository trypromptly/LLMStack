import base64
import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.llm.openai import (
    OpenAIAPIInputEnvironment,
    OpenAIFile,
    OpenAIImageEditsProcessor,
    OpenAIImageEditsProcessorConfiguration,
    OpenAIImageEditsProcessorInput,
    OpenAIImageEditsProcessorOutput,
    Size,
)
from llmstack.common.utils.utils import get_key_or_raise, validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    IMAGE_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class ImagesEditInput(ApiProcessorSchema):
    image: Optional[str] = Field(
        default="",
        description="The image to edit. Must be a valid PNG file, less than 4MB, and square. If mask is not provided, image must have transparency, which will be used as the mask.",
        json_schema_extra={"maxSize": 4000000, "accepts": {"image/png": []}, "widget": "file"},
    )
    image_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of image",
    )
    prompt: str = Field(
        default="",
        description="The prompt to generate image.",
    )


class ImagesEditOutput(ApiProcessorSchema):
    answer: List[str] = Field(
        default=[],
        description="The generated images.",
        json_schema_extra={"widget": IMAGE_WIDGET_NAME},
    )


class ImagesEditConfiguration(
    OpenAIImageEditsProcessorConfiguration,
    ApiProcessorSchema,
):
    size: Optional[Size] = Field(
        "1024x1024",
        description="The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.",
        example="1024x1024",
        json_schema_extra={"advanced_parameter": False},
    )
    n: Optional[conint(ge=1, le=4)] = Field(
        1,
        description="The number of images to generate. Must be between 1 and 10.",
        example=1,
        json_schema_extra={"advanced_parameter": False},
    )


class ImagesEdit(
    ApiProcessorInterface[ImagesEditInput, ImagesEditOutput, ImagesEditConfiguration],
):
    """
    OpenAI Images Generations API
    """

    @staticmethod
    def name() -> str:
        return "Image Edit"

    @staticmethod
    def slug() -> str:
        return "images_edit"

    @staticmethod
    def description() -> str:
        return "Edit source image with a prompt"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="""{% for image in answer %}
![Generated Image]({{image}})
{% endfor %}""",
        )

    def process(self) -> dict:
        _env = self._env

        prompt = get_key_or_raise(
            self._input.model_dump(),
            "prompt",
            "No prompt found in input",
        )

        image = self._input.image or None
        if (image is None or image == "") and "image_data" in self._input.model_dump():
            image = self._input.image_data
        if image is None or image == "":
            raise Exception("No image found in input")

        # Extract from objref if it is one
        image = self._get_session_asset_data_uri(image)

        mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
            image,
        )
        image_data = base64.b64decode(base64_encoded_data)
        openai_images_edit_input = OpenAIImageEditsProcessorInput(
            env=OpenAIAPIInputEnvironment(
                openai_api_key=get_key_or_raise(
                    _env,
                    "openai_api_key",
                    "No openai_api_key found in _env",
                ),
            ),
            image=OpenAIFile(
                name=file_name,
                content=image_data,
                mime_type=mime_type,
            ),
            mask=None,
            prompt=prompt,
        )
        response: OpenAIImageEditsProcessorOutput = OpenAIImageEditsProcessor(
            self._config.model_dump(),
        ).process(openai_images_edit_input.model_dump())
        async_to_sync(self._output_stream.write)(
            ImagesEditOutput(answer=response.answer),
        )

        output = self._output_stream.finalize()
        return output
