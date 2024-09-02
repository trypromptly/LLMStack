import base64
import json
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


class Cookie(BaseModel):
    name: str
    value: str
    domain: Optional[str] = None


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
    query_params: Optional[str] = Field(
        description="The query parameters to send with the request",
        json_schema_extra={"widget": "textarea"},
        default=None,
    )


class SimpleHTTPProcessorOutput(ApiProcessorSchema):
    response: str = Field(description="The response from the API call as a string", default="")
    response_json: Optional[Dict[str, Any]] = Field(
        description="The response from the API call as a JSON object", default={}
    )
    response_objref: Optional[str] = Field(description="The reference to the response object", default=None)
    headers: Optional[Dict[str, str]] = Field(description="The headers from the API call", default={})
    code: int = Field(description="The status code from the API call", default=200)
    size: int = Field(description="The size of the response from the API call", default=0)
    time: float = Field(description="The time it took to get the response from the API call", default=0.0)


class SimpleHTTPProcessorConfiguration(ApiProcessorSchema):
    method: HTTPMethod = Field(
        description="The HTTP method to use", default=HTTPMethod.GET, json_schema_extra={"advanced_parameter": False}
    )
    query_params: List[KeyVal] = Field(description="The query to send with the request", default=[])
    body: Optional[str] = Field(
        description="The body to send with the request", json_schema_extra={"widget": "textarea"}, default=None
    )
    headers: List[KeyVal] = Field(description="The headers to send with the request", default=[])
    cookies: List[Cookie] = Field(description="The cookies to send with the request", default=[])
    connection_id: Optional[str] = Field(
        default=None,
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
        description="Use your authenticated connection to make the request",
    )
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
        connection = (
            self._env["connections"].get(
                self._config.connection_id,
                None,
            )
            if self._config.connection_id
            else None
        )
        headers = {kv.key: kv.value for kv in self._config.headers}
        query_params = {kv.key: kv.value for kv in self._config.query_params}
        body = json.loads(self._config.body) if self._config.body else {}
        cookie_jar = prequests.requests.cookies.RequestsCookieJar()
        if self._config.cookies:
            for cookie in self._config.cookies:
                if cookie.domain:
                    cookie_jar.set(cookie.name, cookie.value, domain=cookie.domain)
                else:
                    cookie_jar.set(cookie.name, cookie.value)

        if self._input.query_params:
            query_params.update(json.loads(self._input.query_params))

        if self._input.body:
            body.update(json.loads(self._input.body))

        if self._config.method == HTTPMethod.GET:
            response = prequests.get(
                self._input.url, params=query_params, headers=headers, cookies=cookie_jar, _connection=connection
            )
        elif self._config.method == HTTPMethod.POST:
            response = prequests.post(
                self._input.url,
                params=query_params,
                data=body,
                headers=headers,
                cookies=cookie_jar,
                _connection=connection,
            )
        elif self._config.method == HTTPMethod.PUT:
            response = prequests.put(
                self._input.url,
                params=query_params,
                data=body,
                headers=headers,
                cookies=cookie_jar,
                _connection=connection,
            )
        elif self._config.method == HTTPMethod.DELETE:
            response = prequests.delete(
                self._input.url, params=query_params, headers=headers, cookies=cookie_jar, _connection=connection
            )
        elif self._config.method == HTTPMethod.HEAD:
            response = prequests.head(
                self._input.url, params=query_params, headers=headers, cookies=cookie_jar, _connection=connection
            )
        else:
            raise ValueError("Invalid HTTP method")

        objref = None
        response_text = response.text
        if self._config.output_type == OutputType.OBJECT:
            text_data_uri = f"data:text/plain;name={self._input.url};base64,{base64.b64encode(response.text.encode('utf-8')).decode('utf-8')}"
            objref = self._upload_asset_from_url(text_data_uri, self._input.url, "text/plain").objref
            response_text = objref

        response_json = None
        try:
            if response.json():
                response_json = response.json()
                if isinstance(response_json, list):
                    response_json = {"data": response.json()}
        except Exception:
            pass

        async_to_sync(self._output_stream.write)(
            SimpleHTTPProcessorOutput(
                response=response_text,
                response_json=response_json,
                response_objref=objref,
                headers=dict(response.headers),
                code=response.status_code,
                size=len(response.text),
                time=response.elapsed.total_seconds(),
            )
        )

        output = self._output_stream.finalize()
        return output
