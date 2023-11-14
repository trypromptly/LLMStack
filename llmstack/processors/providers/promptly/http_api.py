import json
import requests
from requests.auth import HTTPBasicAuth
from enum import Enum

import logging
from typing import Any, Dict, List, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import Field, HttpUrl, root_validator
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.common.blocks.base.processor import Schema

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
    
class RequestBodyParameterType(ParameterType):
    type: FieldType = Field(default=FieldType.STRING)
    
class HttpAPIProcessorInput(Schema):
    input_data: Optional[str] = Field(description='Input', advanced_parameter=False, widget='textarea')

class HttpAPIProcessorOutput(Schema):
    code: int
    headers: Dict[str, str] = {}
    text: Optional[str] = None
    content_json: Optional[Union[Dict[str, Any], List[Dict]]] = None
    is_ok: bool = False
    url: Optional[str] = None
    encoding: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None
    elapsed: Optional[int] = None


class RequestBody(Schema):
    parameters: List[RequestBodyParameterType] = Field(title='Request body parameters', default=[], advanced_parameter=False)
    
class HttpAPIProcessorConfiguration(Schema):
    path: str = Field(description='Path to append to the URL. You can add a prameter by encolosing it in single brackets {param}', advanced_parameter=False)
    method: HttpMethod = Field(default=HttpMethod.GET, advanced_parameter=False)
    
    openapi_spec: Optional[str] = Field(description='OpenAPI spec', widget='textarea')
    openapi_spec_url: Optional[HttpUrl] = Field(description='URL to the OpenAPI spec')
    parse_openapi_spec: bool = Field(default=True)
    _openapi_spec_parsed: bool = Field(default=False, widget='hidden')

    url: Optional[HttpUrl]  = Field(description='URL to make the request to', advanced_parameter=False)
    parameters: List[ParameterType] = Field(title='Parameters to pass', default=[], advanced_parameter=False)
    request_body: Optional[RequestBody] = Field(default=None, advanced_parameter=False)
    
    connection_id: Optional[str] = Field(widget='connectionselect',  advanced_parameter=False)

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
                parsed_spec = parse_openapi_spec(json.loads(openapi_spec), values['path'], values['method'])
                values.update(parsed_spec)
                values['_openapi_spec_parsed'] = True
        
        schema = {'type' : 'object', 'properties': {}}
        required_fields = []
        for parameter in values['parameters']:
            schema['properties'][parameter.name] = {'type': 'string', 'description': parameter.description}
            if parameter.required:
                required_fields.append(parameter.name)
        if values['request_body']:
            for parameter in values['request_body'].parameters:
                schema['properties'][parameter.name] = {'type': parameter.type, 'description': parameter.description}
                if parameter.required:
                    required_fields.append(parameter.name)
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

    def process(self):
        url = f"{self._config.url}{self._config.path}"
        method = self._config.method
        
        input_data = json.loads(self._input.input_data or '{}')
        params = {}
        headers = {}
        body_data = {}        
        
        requred_parameters = [parameter.name for parameter in self._config.parameters if parameter.required]
        for required_parameter in requred_parameters:
            if required_parameter not in input_data:
                raise Exception(f'Required parameter {required_parameter} not found in input')
        
        # Extract all parameters from the url and replace them with the values from the input
        for param in self._config.parameters:
            if param.location == ParameterLocation.PATH:
                url = url.replace(f'{{{param.name}}}', str(input_data.get(param.name, '')))
            elif param.location == ParameterLocation.QUERY:
                if param.name in input_data:
                    params[param.name] = input_data[param.name]
            elif param.location == ParameterLocation.HEADER:
                if param.name in input_data:
                    headers[param.name] = input_data[param.name]
                    
        if self._config.request_body:
            required_body_parameters = [parameter.name for parameter in self._config.request_body.parameters if parameter.required]
            for required_body_parameter in required_body_parameters:
                if required_body_parameter not in input_data:
                    raise Exception(f'Required parameter {required_body_parameter} not found in input')
        
            for param in self._config.request_body.parameters:
                if param.name in input_data:
                    body_data[param.name] = input_data.get(param.name)
        
        auth = None
        if self._config.connection_id:
            connection = self._env['connections'][self._config.connection_id]
            if connection['base_connection_type'] == 'credentials' and connection['connection_type_slug'] == 'basic_authentication':                
                auth = HTTPBasicAuth(connection['configuration']['username'], 
                                     connection['configuration']['password'])
            elif connection['base_connection_type'] == 'credentials' and connection['connection_type_slug'] == 'bearer_authentication':
                headers["Authorization"] = f"{connection['configuration']['token_prefix']} {connection['configuration']['token']}"
            elif connection['base_connection_type'] == 'oauth2':
                 headers["Authorization"] = f"Bearer {connection['configuration']['token']}"
                
        if method == HttpMethod.GET:
            logger.info(f"Making GET request to {url}")
            response = requests.get(url=url, 
                                    headers=headers,
                                    params=params,
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
            
        elif method == HttpMethod.POST:
            response = requests.post(url=url,
                                     headers=headers,
                                     params=params,
                                     data=body_data,
                                     timeout=self._config.timeout,
                                     auth=auth,
                                     allow_redirects=self._config.allow_redirects)
            content_json = None
            try:
                content_json = response.json()
            except:
                pass
            
            async_to_sync(self._output_stream.write)(HttpAPIProcessorOutput(
                code=200,
                is_ok=True,
                text=response.text,
                content_json=content_json,
                encoding=response.encoding,
                cookies=response.cookies,
                elapsed=response.elapsed.total_seconds(),
                url=response.url,
                headers=dict(response.headers),
            ))
        elif method == HttpMethod.PUT:
            response = requests.put(url=url,
                                    params=params,
                                    data=body_data,
                                    timeout=self._config.timeout,
                                    auth=None,
                                    allow_redirects=self._config.allow_redirects)
            
        else:
            raise NotImplementedError
        
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
            parameters=[openapi_parameters_to_ParameterType(parameter) for parameter in method_info['requestBody']['content']['application/json']['schema']['properties'].values()]
        )
    
    return HttpAPIProcessorConfiguration(
        path=path,
        method=HttpMethod(method.upper()),
        url=url,
        parameters=parameters,
        request_body=request_body
    ).dict()