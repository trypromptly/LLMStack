import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import requests
from asgiref.sync import async_to_sync
from pydantic import Field, HttpUrl, root_validator
from requests.auth import HTTPBasicAuth

from llmstack.common.blocks.base.processor import Schema
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, hydrate_input

logger = logging.getLogger(__name__)


class HttpMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

    def __str__(self):
        return self.value

class FieldType(str, Enum):
    STRING = 'string'
    NUMBER = 'number'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'
    ARRAY = 'array'

    def __str__(self):
        return self.value

class ParameterLocation(str, Enum):
    PATH = 'path'
    QUERY = 'query'
    HEADER = 'header'
    COOKIE = 'cookie'

    def __str__(self):
        return self.value

class ParameterType(Schema):
    name: str
    location: ParameterLocation = Field(default=ParameterLocation.PATH)
    required: bool = True
    description: Optional[str] = None
    value: Optional[str] = None

class RequestBodyParameterType(Schema):
    name: str
    type: FieldType = Field(default=FieldType.STRING)
    required: bool = True
    description: Optional[str] = None

class HttpAPIProcessorInput(Schema):
    input_data: Optional[str] = Field(description='Input', advanced_parameter=False, widget='textarea')

class HttpAPIProcessorOutput(Schema):
    code: int = Field(title='Response code', default=200,
                      advanced_parameter=False)
    headers: Dict[str, str] = Field(
        title='Response headers', default={}, advanced_parameter=False)
    text: Optional[str] = Field(
        title='Response text', default=None, advanced_parameter=False)
    content_json: Optional[Union[Dict[str, Any], List[Dict]]] = Field(
        title='Response JSON', default=None, advanced_parameter=False)
    is_ok: bool = Field(title='Is response OK',
                        default=True, advanced_parameter=False)
    url: Optional[str] = Field(
        title='Response URL', default=None, advanced_parameter=False)
    encoding: Optional[str] = Field(
        title='Response encoding', default=None, advanced_parameter=False)
    cookies: Optional[Dict[str, str]] = Field(
        title='Response cookies', default=None, advanced_parameter=False)
    elapsed: Optional[int] = Field(
        title='Response elapsed time', default=None, advanced_parameter=False)

class RequestBody(Schema):
    parameters: List[RequestBodyParameterType] = Field(
        title='Request body parameters', default=[], advanced_parameter=False)

class ContentType(str, Enum):
    JSON = 'application/json'

    def __str__(self):
        return self.value
    
class HttpAPIProcessorConfiguration(Schema):
    url: Optional[HttpUrl] = Field(
        description='URL to make the request to', advanced_parameter=False)
    path: str = Field(
        description='Path to append to the URL. You can add a prameter by encolosing it in single brackets {param}', advanced_parameter=False)
    method: HttpMethod = Field(
        default=HttpMethod.GET, advanced_parameter=False)
    content_type: ContentType = Field(
        default=ContentType.JSON, advanced_parameter=False)

    parameters: List[ParameterType] = Field(
        title='Parameters to pass', default=[], advanced_parameter=False)
    request_body: Optional[RequestBody] = Field(
        default=None, advanced_parameter=False)
    
    connection_id: Optional[str] = Field(
        widget='connection',  advanced_parameter=False, description='Use your authenticated connection to make the request')
    
    body: Optional[str] = Field(
        description='Optional Request body, if not set body will be created from parameters', widget='textarea', advanced_parameter=False)
    
    openapi_spec: Optional[str] = Field(
        description='OpenAPI spec', widget='textarea')
    openapi_spec_url: Optional[HttpUrl] = Field(
        description='URL to the OpenAPI spec')
    parse_openapi_spec: bool = Field(default=True)
    _openapi_spec_parsed: bool = Field(default=False, widget='hidden')

    allow_redirects: Optional[bool] = True
    timeout: Optional[float] = Field(default=5, advanced_parameter=True)

    _schema: Optional[str] = None

    @root_validator
    def validate_input(cls, values):
        openapi_spec = values.get('openapi_spec', None)
        openapi_spec_url = values.get('openapi_spec_url', None)
        if values.get('parse_openapi_spec', False) == True and not values.get('_openapi_spec_parsed', False):
            if openapi_spec_url:
                response = requests.get(openapi_spec_url)
                openapi_spec = response.text
            if openapi_spec:
                parsed_spec = parse_openapi_spec(json.loads(
                    openapi_spec), values['path'], values['method'])
                values.update(parsed_spec)
                values['_openapi_spec_parsed'] = True

        schema = {'type': 'object', 'properties': {}}
        required_fields = []
        for parameter in values['parameters']:
            param_name = f'{parameter.location}_{parameter.name}'
            schema['properties'][param_name] = {
                'type': 'string', 'description': parameter.description}
            if parameter.required:
                required_fields.append(param_name)
                
        if values['request_body']:
            for parameter in values['request_body'].parameters:
                param_name = f'body_{parameter.name}'
                schema['properties'][param_name] = {
                    'type': parameter.type, 'description': parameter.description}
                if parameter.required:
                    required_fields.append(param_name)
                    
        schema['required'] = required_fields
        values['_schema'] = json.dumps(schema)
        return values


class PromptlyHttpAPIProcessor(ApiProcessorInterface[HttpAPIProcessorInput, HttpAPIProcessorOutput, HttpAPIProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'HTTP API Processor'

    @staticmethod
    def slug() -> str:
        return 'http_api_processor'

    @staticmethod
    def description() -> str:
        return 'Makes a HTTP request to the specified URL'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def session_data_to_persist(self) -> dict:
        return {}

    @classmethod
    def get_tool_input_schema(cls, processor_data) -> dict:
        if 'config' in processor_data and '_schema' in processor_data['config']:
            return json.loads(processor_data['config']['_schema'])

        return json.loads(cls.get_input_schema())

    def tool_invoke_input(self, tool_args: dict):
        return HttpAPIProcessorInput(input_data=json.dumps(tool_args))

    def process(self):
        input_json = json.loads(self._input.input_data or '{}')
        
        path_params = {}
        query_params = {}
        headers = {}
        cookies = {}
        body_data = {}
        
        for param_key in input_json:
            if param_key.startswith('path_'):
                path_params[param_key[5:]] = input_json[param_key]
            elif param_key.startswith('query_'):
                query_params[param_key[6:]] = input_json[param_key]
            elif param_key.startswith('header_'):
                headers[param_key[7:]] = input_json[param_key]
            elif param_key.startswith('body_'):
                body_data[param_key[5:]] = input_json[param_key]
            elif param_key.startswith('cookie_'):
                cookies[param_key[7:]] = input_json[param_key]
            
        auth = None
        method = self._config.method
        
        connection_configuration = {}
        if self._config.connection_id:
            connection = self._env['connections'][self._config.connection_id]
            connection_type = connection['base_connection_type']
    
            if connection_type == 'credentials':
                type_slug = connection['connection_type_slug']
                if type_slug == 'basic_authentication':
                    auth = HTTPBasicAuth(connection['configuration']['username'],
                                         connection['configuration']['password'])
                elif type_slug == 'bearer_authentication':
                    headers["Authorization"] = f"{connection['configuration']['token_prefix']} {connection['configuration']['token']}"
                elif type_slug == 'api_key_authentication' and connection['configuration']['header_key']:
                    headers[connection['configuration']['header_key']] = connection['configuration']['api_key']
            elif connection_type == 'oauth2':
                headers["Authorization"] = f"Bearer {connection['configuration']['token']}"
            
            connection_configuration = connection['configuration']
        
        url = f'{self._config.url}{self._config.path}'
        url = hydrate_input(url, {'_parameters' : path_params, '_connection' : connection_configuration})    
        
        if self._config:
            for parameter in self._config.parameters:
                if not parameter.required:
                    continue
                if parameter.location == ParameterLocation.PATH and parameter.name not in path_params:
                    raise Exception(
                        f'Required parameter {parameter.name} not found in input')
                if parameter.location == ParameterLocation.QUERY and parameter.name not in query_params:
                    raise Exception(
                        f'Required parameter {parameter.name} not found in input')
                if parameter.location == ParameterLocation.HEADER and parameter.name not in headers:
                    raise Exception(
                        f'Required parameter {parameter.name} not found in input')
                if parameter.location == ParameterLocation.COOKIE and parameter.name not in cookies:
                    raise Exception(
                        f'Required parameter {parameter.name} not found in input')

        if self._config.request_body:
            for parameter in self._config.request_body.parameters:
                if not parameter.required:
                    continue
                if parameter.name not in body_data:
                    raise Exception(
                        f'Required parameter {parameter.name} not found in input')

        # Check if user has provided their own body
        if self._config.body:
            headers['Content-Type'] = self._config.content_type.value
            body = self._config.body
            body = hydrate_input(body, {'_parameters' : body_data, '_connection' : connection_configuration})
            body_data = bytes(body, 'utf-8')          
        
        http_method = str(method).lower()        
        response = requests.request(http_method, 
                                    url=url, 
                                    headers=headers,
                                    params=query_params,
                                    data=body_data,
                                    cookies=cookies,
                                    timeout=self._config.timeout,
                                    auth=auth,
                                    allow_redirects=self._config.allow_redirects)
        content_json = None
        try:
            content_json = response.json()
        except:
            pass
        
        async_to_sync(self._output_stream.write)(HttpAPIProcessorOutput(
                code=response.status_code,
                is_ok=response.ok,
                text=response.text,
                content_json=content_json,
                encoding=response.encoding,
                cookies=response.cookies,
                elapsed=response.elapsed.total_seconds(),
                url=response.url,
                headers=dict(response.headers),
            ))
        output = self._output_stream.finalize()
        return output


def parse_openapi_spec(spec_dict, path, method) -> dict:
    def openapi_parameters_to_ParameterType(parameter) -> ParameterType:
        return ParameterType(
            name=parameter['name'],
            location=ParameterLocation(parameter['in']),
            required=parameter['required'],
            description=parameter.get('description')
        )

    url = None
    path_info = None
    version = None
    method_info = None
    parameters = []
    request_body = None
    protocol = None

    for path_key, path_data in spec_dict["paths"].items():
        if path_key == path:
            path_info = path_data
            break

    if not path_info:
        raise Exception(f'Path {path} not found in OpenAPI spec')

    # Get spec version
    version = spec_dict.get('openapi')
    if not version:
        version = spec_dict.get('swagger')
        if not version:
            raise Exception('OpenAPI spec version not found')

    protocol = spec_dict.get('schemes', ['https'])[0]
    # Get server url
    if 'servers' in spec_dict:
        url = f"{protocol}://{spec_dict['servers'][0]['url']}"
    if 'host' in spec_dict:
        url = f"{protocol}://{spec_dict['host']}"

    # Get method info
    for method_key, method_data in path_info.items():
        if method_key == method.lower():
            method_info = method_data
            break

    if not method_info:
        raise Exception(f'Method {method} not found in OpenAPI spec')

    # Get parameters
    for parameter in method_info.get('parameters', []):
        parameters.append(openapi_parameters_to_ParameterType(parameter))

    # Get request body
    if method_info.get('requestBody'):
        request_body = RequestBody(
            parameters=[openapi_parameters_to_ParameterType(
                parameter) for parameter in method_info['requestBody']['content']['application/json']['schema']['properties'].values()]
        )

    return HttpAPIProcessorConfiguration(
        path=path,
        method=HttpMethod(method.upper()),
        url=url,
        parameters=parameters,
        request_body=request_body
    ).dict()
