import logging
from enum import Enum
from typing import List, Optional

import openai
from asgiref.sync import async_to_sync
from pydantic import Field, conint

from llmstack.processors.providers.api_processor_interface import (
    IMAGE_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class ResponseFormat(str, Enum):
    url = "url"
    b64_json = "b64_json"

    def __str__(self):
        return self.value


class ImageModel(str, Enum):
    DALL_E_3 = "dall-e-3"
    DALL_E_2 = "dall-e-2"

    def __str__(self):
        return self.value


class Size(str, Enum):
    field_256x256 = "256x256"
    field_512x512 = "512x512"
    field_1024x1024 = "1024x1024"
    field_1024x1792 = "1024x1792"
    field_1792x1024 = "1792x1024"

    def __str__(self):
        return self.value


class Quality(str, Enum):
    standard = "standard"
    hd = "hd"

    def __str__(self):
        return self.value


class ImagesGenerationsInput(ApiProcessorSchema):
    prompt: str = Field(
        ...,
        description="A text description of the desired image(s). The maximum length is 1000 characters.",
        example="A cute baby sea otter",
    )


class ImagesGenerationsOutput(ApiProcessorSchema):
    data: List[str] = Field(
        default=[],
        description="The generated images.",
        widget=IMAGE_WIDGET_NAME,
    )


class ImagesGenerationsConfiguration(ApiProcessorSchema):
    model: Optional[ImageModel] = Field(
        default=ImageModel.DALL_E_2,
        description="Select the model to use",
        advanced_parameter=False,
    )
    size: Optional[Size] = Field(
        "1024x1024",
        description="The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.",
        example="1024x1024",
        advanced_parameter=False,
    )
    n: Optional[conint(ge=1, le=4)] = Field(
        1,
        description="The number of images to generate. Must be between 1 and 10.",
        example=1,
        advanced_parameter=False,
    )
    response_format: Optional[ResponseFormat] = Field(
        "url",
        description="The format in which the generated images are returned. Must be one of `url` or `b64_json`.",
        example="url",
    )
    quality: Optional[Quality] = Field(
        default=Quality.standard,
        description="The quality of the generated images. Must be one of `standard` or `hd`.",
    )


class ImagesGenerations(
    ApiProcessorInterface[ImagesGenerationsInput, ImagesGenerationsOutput, ImagesGenerationsConfiguration],
):

    """
    OpenAI Images Generations API
    """

    @staticmethod
    def name() -> str:
        return "Image Generations"

    @staticmethod
    def slug() -> str:
        return "image_generations"

    @staticmethod
    def description() -> str:
        return "Generates images from a given prompt"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    def process(self) -> dict:
        _env = self._env
        prompt = self._input.prompt

        if not prompt:
            raise Exception("No prompt found in input")

        client = openai.OpenAI(api_key=_env["openai_api_key"])
        result = client.images.generate(
            prompt=prompt,
            model=self._config.model,
            size=self._config.size,
            n=self._config.n,
            quality=self._config.quality,
            response_format=self._config.response_format,
        )

        async_to_sync(self._output_stream.write)(
            ImagesGenerationsOutput(
                data=[image.b64_json or image.url for image in result.data],
            ),
        )

        output = self._output_stream.finalize()

        return output
