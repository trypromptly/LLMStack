import base64
import logging
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import conint
from pydantic import Field

from common.blocks.llm.openai import OpenAIAPIInputEnvironment
from common.blocks.llm.openai import OpenAIFile
from common.blocks.llm.openai import OpenAIImageEditsProcessor
from common.blocks.llm.openai import OpenAIImageEditsProcessorConfiguration
from common.blocks.llm.openai import OpenAIImageEditsProcessorInput
from common.blocks.llm.openai import OpenAIImageEditsProcessorOutput
from common.blocks.llm.openai import Size
from common.utils.utils import get_key_or_raise
from common.utils.utils import validate_parse_data_uri
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import ApiProcessorSchema
from processors.providers.api_processor_interface import DataUrl
from processors.providers.api_processor_interface import IMAGE_WIDGET_NAME

logger = logging.getLogger(__name__)


class ImagesEditInput(ApiProcessorSchema):
    image: Optional[str] = Field(
        default='',
        description='The image to edit. Must be a valid PNG file, less than 4MB, and square. If mask is not provided, image must have transparency, which will be used as the mask.',
        accepts={'image/png': []},
        maxSize=4000000,
        widget='file',
    )
    image_data: Optional[str] = Field(
        default='', description='The base64 encoded data of image', pattern=r'data:(.*);name=(.*);base64,(.*)',
    )
    prompt: str = Field(
        default='', description='The prompt to generate image.',
    )


class ImagesEditOutput(ApiProcessorSchema):
    answer: List[str] = Field(
        default=[], description='The generated images.', widget=IMAGE_WIDGET_NAME,
    )


class ImagesEditConfiguration(OpenAIImageEditsProcessorConfiguration, ApiProcessorSchema):
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


class ImagesEdit(ApiProcessorInterface[ImagesEditInput, ImagesEditOutput, ImagesEditConfiguration]):
    """
    OpenAI Images Generations API
    """
    def name() -> str:
        return 'open ai/images_edit'

    def slug() -> str:
        return 'openai_images_edit'

    def process(self) -> dict:
        _env = self._env

        prompt = get_key_or_raise(
            self._input.dict(), 'prompt', 'No prompt found in input',
        )

        image = self._input.image or None
        if (image is None or image == '') and 'image_data' in self._input.dict():
            image = self._input.image_data
        if image is None or image == '':
            raise Exception('No image found in input')

        mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
            image,
        )
        image_data = base64.b64decode(base64_encoded_data)
        openai_images_edit_input = OpenAIImageEditsProcessorInput(
            env=OpenAIAPIInputEnvironment(
                openai_api_key=get_key_or_raise(
                _env, 'openai_api_key', 'No openai_api_key found in _env',
                ),
            ),
            image=OpenAIFile(
                name=file_name, content=image_data,
                mime_type=mime_type,
            ),
            mask=None,
            prompt=prompt,
        )
        response: OpenAIImageEditsProcessorOutput = OpenAIImageEditsProcessor(
            self._config.dict(),
        ).process(openai_images_edit_input.dict())
        async_to_sync(self._output_stream.write)(
            ImagesEditOutput(answer=response.answer),
        )

        output = self._output_stream.finalize()
        return output
