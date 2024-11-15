import logging
from typing import Any, Dict, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.prequests import post
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType

logger = logging.getLogger(__name__)


class CaptionImageProcessorInput(ApiProcessorSchema):
    template_id: Optional[str] = Field(description="Template Id", default=None)
    top_text: Optional[str] = Field(description="The text to put on the top of the image", default=None)
    bottom_text: Optional[str] = Field(description="The text to put on the bottom of the image", default=None)


class CaptionImageProcessorOutput(ApiProcessorSchema):
    response: str = Field(description="The response from the API call as a string", default="")
    response_json: Optional[Dict[str, Any]] = Field(
        description="The response from the API call as a JSON object", default={}
    )
    response_objref: Optional[str] = Field(description="The reference to the response object", default=None)
    headers: Optional[Dict[str, str]] = Field(description="The headers from the API call", default={})
    code: int = Field(description="The status code from the API call", default=200)
    size: int = Field(description="The size of the response from the API call", default=0)
    time: float = Field(description="The time it took to get the response from the API call", default=0.0)


class CaptionImageProcessorConfiguration(ApiProcessorSchema):
    pass


class CaptionImageProcessor(
    ApiProcessorInterface[CaptionImageProcessorInput, CaptionImageProcessorOutput, CaptionImageProcessorConfiguration],
):
    """
    Caption an image.
    """

    @staticmethod
    def name() -> str:
        return "Caption an image"

    @staticmethod
    def slug() -> str:
        return "caption_image"

    @staticmethod
    def description() -> str:
        return "Caption an image."

    @staticmethod
    def provider_slug() -> str:
        return "imgflip"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{response}}",
            jsonpath="$.response",
        )

    async def process(self) -> dict:
        provider_config = self.get_provider_config(provider_slug=self.provider_slug(), processor_slug="*")
        deployment_config = self.get_provider_config(provider_slug=self.provider_slug(), processor_slug="*")

        username = deployment_config.username
        password = deployment_config.password
        template_id = self._input.template_id
        text0 = self._input.top_text
        text1 = self._input.bottom_text

        response = post(
            url="https://api.imgflip.com/caption_image",
            params={
                "template_id": template_id,
                "username": username,
                "password": password,
                "boxes[0][text]": text0,
                "boxes[1][text]": text1,
            },
        )
        async_to_sync(self._output_stream.write)(
            CaptionImageProcessorOutput(
                response=response.text,
                response_json=response.json(),
                code=response.status_code,
                size=len(response.text),
                time=response.elapsed.total_seconds(),
            )
        )
        self._usage_data.append(
            (
                f"{self.provider_slug()}/*/*/*",
                MetricType.API_INVOCATION,
                (provider_config.provider_config_source, 1),
            )
        )
        return self._output_stream.output.finalize()
