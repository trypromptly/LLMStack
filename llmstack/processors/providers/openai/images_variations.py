import base64
import logging
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import conint
from pydantic import Field

from llmstack.common.blocks.llm.openai import OpenAIAPIInputEnvironment, OpenAIFile, OpenAIImageVariationsProcessor, OpenAIImageVariationsProcessorConfiguration, OpenAIImageVariationsProcessorInput, OpenAIImageVariationsProcessorOutput, Size
from llmstack.common.utils.utils import get_key_or_raise, validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema, IMAGE_WIDGET_NAME

logger = logging.getLogger(__name__)


class ImagesVariationsInput(ApiProcessorSchema):
    image: Optional[str] = Field(
        default='', description='The image to use as the basis for the variation(s). Must be a valid PNG file, less than 4MB, and square.', accepts={'image/png': []}, maxSize=4000000, widget='file',
    )
    image_data: Optional[str] = Field(
        default='', description='The base64 encoded data of image', pattern=r'data:(.*);name=(.*);base64,(.*)',
    )


class ImagesVariationsOutput(ApiProcessorSchema):
    answer: List[str] = Field(
        default=[], description='The generated images.', widget=IMAGE_WIDGET_NAME,
    )


class ImagesVariationsConfiguration(OpenAIImageVariationsProcessorConfiguration, ApiProcessorSchema):
    size: Optional[Size] = Field(
        '1024x1024',
        description='The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.',
        example='1024x1024',
        advanced_parameter=False,
    )
    n: Optional[conint(ge=1, le=4)] = Field(
        1,
        description='The number of images to generate. Must be between 1 and 10.',
        example=1,
        advanced_parameter=False,
    )


class ImagesVariations(ApiProcessorInterface[ImagesVariationsInput, ImagesVariationsOutput, ImagesVariationsConfiguration]):
    """
    OpenAI Images Generations API
    """
    @staticmethod
    def name() -> str:
        return 'Image Variations'

    @staticmethod
    def slug() -> str:
        return 'images_variations'

    @staticmethod
    def provider_slug() -> str:
        return 'openai'

    def process(self) -> dict:
        image = self._input.image or None

        if (image is None or image == '') and 'image_data' in self._input.dict():
            image = self._input.image_data
        if image is None or image == '':
            raise Exception('No image found in input')

        mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
            image,
        )

        image_data = base64.b64decode(base64_encoded_data)
        image_variations_api_processor_input = OpenAIImageVariationsProcessorInput(
            env=OpenAIAPIInputEnvironment(
                openai_api_key=get_key_or_raise(
                    self._env, 'openai_api_key', 'No openai_api_key found in _env',
                ),
            ),
            image=OpenAIFile(name=file_name, content=image_data,
                             mime_type=mime_type),
        )
        response: OpenAIImageVariationsProcessorOutput = OpenAIImageVariationsProcessor(
            configuration=self._config.dict(
            ),
        ).process(image_variations_api_processor_input.dict())

        async_to_sync(self._output_stream.write)(
            ImagesVariationsOutput(answer=response.answer),
        )
        output = self._output_stream.finalize()

        return output
