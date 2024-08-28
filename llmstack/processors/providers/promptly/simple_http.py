import logging
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils import prequests
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class KeyVal(BaseModel):
    key: str
    value: str


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"


class SimpleHTTPProcessorInput(ApiProcessorSchema):
    url: str = Field(
        description="The URL to fetch", json_schema_extra={"widget": "textarea"}, default="https://www.google.com"
    )
    body: Optional[str] = Field(
        description="The body of the request", json_schema_extra={"widget": "textarea"}, default=None
    )


class SimpleHTTPProcessorOutput(ApiProcessorSchema):
    response: str = ""
    headers: List[KeyVal] = []
    code: int = 200
    size: int = 0
    time: float = 0.0


class SimpleHTTPProcessorConfiguration(ApiProcessorSchema):
    method: HTTPMethod = Field(
        description="The HTTP method to use", default=HTTPMethod.GET, json_schema_extra={"advanced_parameter": False}
    )
    headers: List[KeyVal] = []


class SimpleHTTPProcessor(
    ApiProcessorInterface[SimpleHTTPProcessorInput, SimpleHTTPProcessorOutput, SimpleHTTPProcessorConfiguration],
):
    """
    Simple HTTP processor
    """

    @staticmethod
    def name() -> str:
        return "Simple HTTP Processor"

    @staticmethod
    def slug() -> str:
        return "simple_http"

    @staticmethod
    def description() -> str:
        return "HTTP Processor"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{response}}",
        )

    def process(self) -> dict:
        if self._config.method == HTTPMethod.GET:
            response = prequests.get(self._input.url)
        elif self._config.method == HTTPMethod.POST:
            response = prequests.post(self._input.url, data=self._input.body)
        elif self._config.method == HTTPMethod.PUT:
            response = prequests.put(self._input.url, data=self._input.body)
        elif self._config.method == HTTPMethod.DELETE:
            response = prequests.delete(self._input.url)
        elif self._config.method == HTTPMethod.HEAD:
            response = prequests.head(self._input.url)
        else:
            raise ValueError("Invalid HTTP method")

        async_to_sync(self._output_stream.write)(
            SimpleHTTPProcessorOutput(
                response=response.text,
                headers=[KeyVal(key=k, value=v) for k, v in response.headers.items()],
                code=response.status_code,
                size=len(response.text),
                time=response.elapsed.total_seconds(),
            )
        )

        output = self._output_stream.finalize()
        return output
