import json
import logging
from enum import Enum
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Union

import requests
from pydantic import Field
from pydantic import HttpUrl

from common.blocks.base.processor import BaseConfiguration
from common.blocks.base.processor import BaseInput
from common.blocks.base.processor import BaseOutput
from common.blocks.base.processor import BaseProcessor
from common.blocks.base.processor import Schema

logger = logging.getLogger(__name__)


class HttpMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    HEAD = 'HEAD'

    def __str__(self):
        return self.value


class NoAuth(Schema):
    _type = 'no_auth'


class APIKeyAuth(Schema):
    _type = 'api_key'
    api_key: str


class BearerTokenAuth(Schema):
    _type = 'bearer_token'
    token: str


class JWTBearerAuth(Schema):
    _type = 'jwt_bearer_token'
    token: str


class BasicAuth(Schema):
    _type = 'basic_auth'
    username: str
    password: str


class OAuth2(Schema):
    _type = 'oauth2'
    access_token: str
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


class EmptyBody(Schema):
    _type = 'empty'


class FormBody(Schema):
    _type: str = 'form'
    form_body: Dict[str, Any]


class RawRequestBody(Schema):
    _type: str = 'raw'
    data: Any
    files: Any


class TextBody(Schema):
    _type: str = 'text'
    text_body: str


class JsonBody(Schema):
    _type: str = 'json'
    json_body: Union[str, Dict]


class XMLBody(Schema):
    _type: str = 'xml'
    xml_body: str


class JavascriptBody(Schema):
    _type: str = 'javascript'
    javascript_body: str


class HTMLBody(Schema):
    _type: str = 'html'
    html_body: str


class HttpAPIProcessorInput(BaseInput):
    url: HttpUrl
    method: HttpMethod = HttpMethod.GET
    headers: Optional[Dict[str, str]] = {}
    authorization: Union[
        APIKeyAuth,
        BearerTokenAuth,
        JWTBearerAuth,
        BasicAuth,
        OAuth2,
        NoAuth,
    ] = Field(default=NoAuth())

    body: Union[
        TextBody,
        JsonBody,
        FormBody,
        XMLBody,
        JavascriptBody,
        HTMLBody,
        RawRequestBody,
        EmptyBody,
    ] = Field(default=EmptyBody())


class HttpAPIProcessorOutput(BaseOutput):
    code: int
    headers: Dict[str, str] = {}
    text: Optional[str] = None
    content: Optional[bytes] = None
    content_json: Optional[Union[Dict[str, Any], List[Dict]]] = None
    is_ok: bool = False
    url: Optional[str] = None
    encoding: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None
    elapsed: Optional[int] = None


class HttpAPIProcessorConfiguration(BaseConfiguration):
    allow_redirects: Optional[bool] = True
    timeout: Optional[float] = 1


class HttpAPIError(Schema):
    code: int
    message: str

class BaseErrorOutput(Schema):
    error: Optional[HttpAPIError] = Field(None, description='Error Object')
    
class HttpAPIProcessor(BaseProcessor[HttpAPIProcessorInput, HttpAPIProcessorOutput, HttpAPIProcessorConfiguration]):
    """
    # HttpAPIProcessor

    The `HttpAPIProcessor` is a processor designed to handle HTTP API requests and is capable of handling various authentication and body types. It simplifies the process of sending requests and processing responses in a consistent manner.

    ## Classes

    ### HttpMethod

    This enumeration class represents the HTTP methods that can be used in requests.

    Values:

    - `GET`
    - `POST`
    - `PUT`
    - `PATCH`
    - `DELETE`
    - `OPTIONS`
    - `HEAD`

    ### Authentication Classes

    The following classes represent different types of authentication that can be used in requests:

    - `NoAuth`: No authentication is used.
    - `APIKeyAuth`: API key authentication with an `api_key` attribute.
    - `BearerTokenAuth`: Bearer token authentication with a `token` attribute.
    - `JWTBearerAuth`: JWT bearer token authentication with a `token` attribute.
    - `BasicAuth`: Basic authentication with `username` and `password` attributes.
    - `OAuth2`: OAuth2 authentication with `access_token`, `token_type`, `expires_in`, and `refresh_token` attributes.

    ### Body Classes

    The following classes represent different types of request bodies that can be used in requests:

    - `EmptyBody`: No request body.
    - `FormBody`: Form data as request body with a `form_body` attribute.
    - `RawRequestBody`: Raw request body data with `data` and `files` attributes.
    - `TextBody`: Text request body with a `text_body` attribute.
    - `JsonBody`: JSON request body with a `json_body` attribute.
    - `XMLBody`: XML request body with an `xml_body` attribute.
    - `JavascriptBody`: Javascript request body with a `javascript_body` attribute.
    - `HTMLBody`: HTML request body with an `html_body` attribute.

    ### HttpAPIProcessorInput

    This class inherits from `BaseInput` and represents the input for the HttpAPIProcessor.

    Attributes:

    - `url`: The HTTP URL for the request.
    - `method`: The HTTP method for the request.
    - `headers`: A dictionary of HTTP headers for the request.
    - `authorization`: One of the authentication classes for the request.
    - `body`: One of the body classes for the request.

    ### HttpAPIProcessorOutput

    This class inherits from `BaseOutput` and represents the output of the HttpAPIProcessor.

    Attributes:

    - `code`: The HTTP status code of the response.
    - `headers`: A dictionary of HTTP headers from the response.
    - `text`: The response text.
    - `content`: The response content as bytes.
    - `content_json`: The response content as JSON (if applicable).
    - `is_ok`: A boolean indicating if the response status is OK.

    ### HttpAPIProcessorConfiguration

    This class inherits from `BaseConfiguration` and represents the configuration for the HttpAPIProcessor.

    Attributes:

    - `allow_redirects`: An optional boolean indicating if redirects are allowed (default: True).
    - `timeout`: An optional float representing the request timeout (default: 1).

    ### HttpAPIError

    This class inherits from `BaseError` and represents an error for the HttpAPIProcessor.

    Attributes:

    - `code`: The error code.
    - `message`: The error message.

    ### HttpAPIProcessor

    This class inherits from `BaseProcessor` and represents the main processor for handling HTTP API requests. It uses the input, output, and configuration classes defined above, and provides methods for processing requests and handling exceptions.
        """
    @staticmethod
    def name() -> str:
        return 'http_api_processor'

    def _process_exception(self, ex: Exception) -> BaseErrorOutput:
        return BaseErrorOutput(error=HttpAPIError(code=500, message=str(ex)))

    def _update_auth_headers(self, headers: Dict[str, str], authorization: Union[APIKeyAuth, BearerTokenAuth, JWTBearerAuth, BasicAuth, OAuth2, NoAuth]) -> Dict[str, str]:
        if (isinstance(authorization, APIKeyAuth)):
            headers['Authorization'] = f'Apikey {authorization.api_key}'
        elif (isinstance(authorization, BearerTokenAuth)) or (isinstance(authorization, JWTBearerAuth)):
            headers['Authorization'] = f'Bearer {authorization.token}'
        elif (isinstance(authorization, BasicAuth)):
            auth = (
                authorization.username,
                authorization.password,
            )
        elif isinstance(authorization, OAuth2):
            raise NotImplemented()
        elif isinstance(authorization, NoAuth):
            pass
        else:
            raise Exception('Invalid authorization type')

        return headers

    def _update_request_params(self, input: HttpAPIProcessorInput, headers: Dict[str, str]) -> Any:
        data = None
        json_body = None
        files = None
        if isinstance(input.body, EmptyBody):
            data = None
        elif isinstance(input.body, FormBody):
            raise Exception('FormBody not implemented')
        elif isinstance(input.body, RawRequestBody):
            data = input.body.data
            files = input.body.files
        elif isinstance(input.body, TextBody):
            data = input.body.text_body
            headers['Content-Type'] = 'text/plain'
        elif isinstance(input.body, JsonBody):
            if isinstance(input.body.json_body, str):
                json_body = json.loads(input.body.json_body)
            else:
                json_body = input.body.json_body
            headers['Content-Type'] = 'application/json'
        elif isinstance(input.body, XMLBody):
            data = input.body.xml_body
            headers['Content-Type'] = 'application/xml'
        elif isinstance(input.body, JavascriptBody):
            data = input.body.javascript_body
            headers['Content-Type'] = 'application/javascript'
        elif isinstance(input.body, HTMLBody):
            data = input.body.html_body
            headers['Content-Type'] = 'text/html'
        else:
            raise Exception('Unknown body type')

        return (data, json_body, files, headers)

    def _process_iter(self, input: HttpAPIProcessorInput, configuration: HttpAPIProcessorConfiguration) -> Generator[HttpAPIProcessorOutput, None, None]:
        response = None
        headers = input.headers.copy()

        headers = self._update_auth_headers(headers, input.authorization)
        method = input.method
        url = input.url
        data, json_body, files, headers = self._update_request_params(
            input, headers,
        )
        timeout = self.configuration.timeout
        allow_redirects = self.configuration.allow_redirects

        response = requests.request(
            method=method,
            url=url,
            data=data,
            json=json_body,
            files=files,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=True,
        )

        if response is None:
            raise Exception('Response is empty')

        iter_lines = response.iter_lines()
        for line in iter_lines:
            if line:
                yield HttpAPIProcessorOutput(
                    code=response.status_code,
                    content=line,
                    text=line.decode(response.encoding),
                    content_json=None,
                    is_ok=response.ok,
                    headers=response.headers,
                    encoding=response.encoding,
                    url=response.url,
                    cookies=response.cookies.get_dict(),
                    elapsed=response.elapsed.total_seconds(),
                )

    def _process(self, input: HttpAPIProcessorInput, configuration: HttpAPIProcessorConfiguration) -> HttpAPIProcessorOutput:
        response = None
        headers = input.headers.copy()

        headers = self._update_auth_headers(headers, input.authorization)
        method = input.method
        url = input.url
        data, json_body, files, headers = self._update_request_params(
            input, headers,
        )
        timeout = self.configuration.timeout
        allow_redirects = self.configuration.allow_redirects

        response = requests.request(
            method=method,
            url=url,
            data=data,
            json=json_body,
            files=files,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=False,
        )

        if response is None:
            raise Exception('Response is empty')

        try:
            json_response = response.json()
        except:
            json_response = None
        return HttpAPIProcessorOutput(
            code=response.status_code,
            content=response.content,
            text=response.text,
            content_json=json_response,
            is_ok=response.ok,
            headers=response.headers,
            encoding=response.encoding,
            url=response.url,
            cookies=response.cookies.get_dict(),
            elapsed=response.elapsed.total_seconds(),
        )
