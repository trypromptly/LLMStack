import base64
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

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


class OutputType(str, Enum):
    STRING = "STRING"
    JSON = "JSON"
    OBJECT = "OBJECT"


class SimpleHTTPProcessorInput(ApiProcessorSchema):
    url: str = Field(
        description="The URL to fetch", json_schema_extra={"widget": "textarea"}, default="https://www.google.com"
    )
    body: Optional[str] = Field(
        description="The body for the request", json_schema_extra={"widget": "textarea"}, default=None
    )


class SimpleHTTPProcessorOutput(ApiProcessorSchema):
    response: str = Field(description="The response from the API call as a string", default="")
    response_json: Optional[Dict[str, Any]] = Field(
        description="The response from the API call as a JSON object", default={}
    )
    response_objref: Optional[str] = Field(description="The reference to the response object", default=None)
    headers: List[KeyVal] = Field(description="The headers from the API call", default=[])
    code: int = Field(description="The status code from the API call", default=200)
    size: int = Field(description="The size of the response from the API call", default=0)
    time: float = Field(description="The time it took to get the response from the API call", default=0.0)


class SimpleHTTPProcessorConfiguration(ApiProcessorSchema):
    method: HTTPMethod = Field(
        description="The HTTP method to use", default=HTTPMethod.GET, json_schema_extra={"advanced_parameter": False}
    )
    headers: List[KeyVal] = Field(description="The headers to send with the request", default=[])
    output_type: OutputType = Field(description="The type of output to return", default=OutputType.STRING)


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

        objref = None
        response_text = response.text
        if self._config.output_type == OutputType.OBJECT:
            text_data_uri = f"data:text/plain;name={self._input.url};base64,{base64.b64encode(response.text.encode('utf-8')).decode('utf-8')}"
            objref = self._upload_asset_from_url(text_data_uri, self._input.url, "text/plain").objref
            response_text = objref

        response_json = None
        if self._config.output_type == OutputType.JSON:
            try:
                response_json = response.json()
            except Exception:
                pass

        async_to_sync(self._output_stream.write)(
            SimpleHTTPProcessorOutput(
                response=response_text,
                response_json=response_json,
                response_objref=objref,
                headers=[KeyVal(key=k, value=v) for k, v in response.headers.items()],
                code=response.status_code,
                size=len(response.text),
                time=response.elapsed.total_seconds(),
            )
        )

        output = self._output_stream.finalize()
        return output
