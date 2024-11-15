import logging
from typing import Any, Dict, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.prequests import get
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class GetMemesProcessorInput(ApiProcessorSchema):
    pass


class GetMemesProcessorOutput(ApiProcessorSchema):
    response: str = Field(description="The response from the API call as a string", default="")
    response_json: Optional[Dict[str, Any]] = Field(
        description="The response from the API call as a JSON object", default={}
    )
    response_objref: Optional[str] = Field(description="The reference to the response object", default=None)
    headers: Optional[Dict[str, str]] = Field(description="The headers from the API call", default={})
    code: int = Field(description="The status code from the API call", default=200)
    size: int = Field(description="The size of the response from the API call", default=0)
    time: float = Field(description="The time it took to get the response from the API call", default=0.0)


class GetMemesProcessorConfiguration(ApiProcessorSchema):
    pass


class GetMemesProcessor(
    ApiProcessorInterface[GetMemesProcessorInput, GetMemesProcessorOutput, GetMemesProcessorConfiguration],
):
    """
    Get memes.
    """

    @staticmethod
    def name() -> str:
        return "Get memes"

    @staticmethod
    def slug() -> str:
        return "get_memes"

    @staticmethod
    def description() -> str:
        return "Get memes."

    @staticmethod
    def provider_slug() -> str:
        return "imgflip"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{response}}",
            jsonpath="$.response",
        )

    def process(self):
        response = get(url="https://api.imgflip.com/get_memes")

        async_to_sync(self._output_stream.write)(
            GetMemesProcessorOutput(
                response=response.text,
                response_json=response.json(),
                headers=dict(response.headers),
                code=response.status_code,
                size=len(response.text),
                time=response.elapsed.total_seconds(),
            )
        )

        return self._output_stream.finalize()
