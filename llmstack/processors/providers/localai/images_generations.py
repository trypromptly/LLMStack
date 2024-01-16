import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.blocks.http import (HttpAPIProcessor,
                                         HttpAPIProcessorInput,
                                         HttpAPIProcessorOutput, HttpMethod,
                                         JsonBody)
from llmstack.common.blocks.llm.openai import Size
from llmstack.processors.providers.api_processor_interface import (
    IMAGE_WIDGET_NAME, ApiProcessorInterface, ApiProcessorSchema)

logger = logging.getLogger(__name__)


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
    base_url: str = Field(description="Base URL", advanced_parameter=False)

    size: Optional[Size] = Field(
        "256x256",
        description="The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.",
        example="1024x1024",
    )
    timeout: int = Field(
        default=60,
        description="Timeout in seconds",
        advanced_parameter=False,
    )


class ImagesGenerations(
    ApiProcessorInterface[ImagesGenerationsInput, ImagesGenerationsOutput, ImagesGenerationsConfiguration],
):
    """
    LocalAI Images Generations API
    """

    @staticmethod
    def name() -> str:
        return "Image Generations"

    @staticmethod
    def slug() -> str:
        return "image_generations"

    @staticmethod
    def description() -> str:
        return "Image generations with LocalAI"

    @staticmethod
    def provider_slug() -> str:
        return "localai"

    def process(self) -> dict:
        prompt = self._input.prompt
        api_request_body = {
            "prompt": self._input.prompt,
        }
        if self._config.size:
            api_request_body["size"] = self._config.size.value

        if not prompt:
            raise Exception("No prompt found in input")

        http_input = HttpAPIProcessorInput(
            url=f"{self._config.base_url}/v1/images/generations",
            method=HttpMethod.POST,
            body=JsonBody(json_body=api_request_body),
        )

        http_api_processor = HttpAPIProcessor(
            {"timeout": self._config.timeout},
        )
        http_response = http_api_processor.process(
            http_input.dict(),
        )
        # If the response is ok, return the choices
        if (
            isinstance(
                http_response,
                HttpAPIProcessorOutput,
            )
            and http_response.is_ok
        ):
            generations = list(
                map(lambda entry: entry["b64_json"], http_response.content_json["data"]),
            )
        else:
            raise Exception(
                "Error in processing request, details: {}".format(
                    http_response.content,
                ),
            )

        async_to_sync(self._output_stream.write)(
            ImagesGenerationsOutput(data=generations),
        )

        output = self._output_stream.finalize()

        return output
