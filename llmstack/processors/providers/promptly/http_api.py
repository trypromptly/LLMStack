import json
import requests
from requests.auth import HTTPBasicAuth
from enum import Enum

import logging
from typing import Any, Dict, List, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import Field, HttpUrl, root_validator
from llmstack.connections.handlers.basic_authentication import BasicAuthenticationBasedAPILogin
from llmstack.connections.handlers.bearer_authentication import BearerAuthenticationBasedAPILogin

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema
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

class ParameterType(Schema):
    name: str
    type: FieldType = Field(default=FieldType.STRING)
    description: str = None
    required: bool = True
    
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


class APIConfiguration(Schema):
    url: Optional[HttpUrl]  = Field(description='URL to make the request to', advanced_parameter=False)
    path: Optional[str] = Field(description='Path to append to the URL. You can add a prameter by encolosing it in single brackets {param}', advanced_parameter=False)
    method: Optional[HttpMethod] = Field(default=HttpMethod.GET, advanced_parameter=False)
    
    path_parameters: List[ParameterType] = Field(default=[], advanced_parameter=False)
    query_parameters: List[ParameterType] = Field(default=[], advanced_parameter=False)
    header_parameters: List[ParameterType] = Field(default=[], advanced_parameter=False)
    cookie_parameters: List[ParameterType] = Field(default=[], advanced_parameter=False)
    body_parameters: List[ParameterType] = Field(default=[], advanced_parameter=False)


class HttpAPIProcessorConfiguration(Schema):
    api_configuration: str = Field(description='API Configuration', advanced_parameter=False, widget='api_configuration')
    
    connection_id: Optional[str] = Field(widget='connectionselect',  advanced_parameter=False)

    allow_redirects: Optional[bool] = True
    timeout: Optional[float] = Field(default=5, advanced_parameter=True)
    
    _schema: Optional[str] = None
    _api_configuration: Optional[APIConfiguration]

    
    @root_validator
    def validate_input(cls, values):
        api_configuration_json = json.loads(values.get('api_configuration'))
        values['_api_configuration'] = APIConfiguration(**api_configuration_json)
        parameters = (api_configuration_json.get('path_parameters') or []) + (api_configuration_json.get('body_parameters') or []) + (api_configuration_json.get('query_parameters') or []) 
        if parameters:
            schema = {'type' : 'object', 'properties': {}}
            properties = {}
            for param in parameters:
                properties[param.name] = {'type': param.type, 'description': param.description}
            schema['properties'] = properties
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
        url = f'{self._config._api_configuration.url}{self._config._api_configuration.path}'
        input_data = json.loads(self._input.input_data or '{}')
        logger.info(f'Input schema: {self._config._schema}')
        # Extract all parameters from the url and replace them with the values from the input
        for param in self._config._api_configuration.path_parameters:
            url = url.replace(f'{{{param.name}}}', str(input_data.get(param.name, '')))
            
        params = {}
        for field in self._config._api_configuration.query_parameters:
            if field.name in self._input.input_data:
                params[field.name] = input_data.get(field.name)
        
        body_data = {}
        for field in self._config._api_configuration.body_parameters:
            if field.name in self._input.input_data:
                body_data[field.name] = input_data.get(field.name)
        
        auth = None
        headers = {}
        if self._config.connection_id:
            connection = self._env['connections'][self._config.connection_id]
            if connection['configuration']['connection_type_slug'] == 'basic_authentication':
                auth = HTTPBasicAuth(connection['configuration']['username'], 
                                     connection['configuration']['password'])
            elif connection['configuration']['connection_type_slug'] == 'bearer_authentication':
                headers["Authorization"] = f"{connection['configuration']['token_prefix']} {connection['configuration']['token']}"
            elif connection['configuration']['connection_type_slug'] == 'oauth2':
                headers["Authorization"] = f"Bearer {connection['configuration']['token']}"
            

        if self._config._api_configuration.method == HttpMethod.GET:

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
        elif self._config._api_configuration.method == HttpMethod.POST:
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
        elif self._config._api_configuration.method == HttpMethod.PUT:
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
    
    def openapi_parameter_to_parameter_type(parameter_dict: dict):
        return ParameterType(
            name=parameter_dict['name'], 
            type=parameter_dict['type'], 
            description=parameter_dict.get('description', ''), 
            required=parameter_dict.get('required', True)).dict()
    
    method = method.upper()
    path_info = None
    for path_key, path_data in spec_dict["paths"].items():
        if path_key == path:
            path_info = path_data
            break
    if not path_info:
        return {}
    
    version = None
    if 'swagger' in spec_dict:
        version = spec_dict['swagger']
    elif 'openapi' in spec_dict:
        version = spec_dict['openapi']
    else:
        raise Exception("Invalid OpenAPI spec")
    
    logger.info(f'Version: {version}')
    if version.startswith('2'):
        url = f"{spec_dict['schemes'][0]}://{spec_dict['host']}"
    elif version.startswith('3'):
        url = f"{spec_dict['schemes'][0]}://spec_dict['servers'][0]['url']"
    
    logger.info(f'URL: {url}')
    
    result = {
        'url': url,
        'path': path,
        'method': method.upper(),
    }
   
    for http_method, method_data in path_info.items():
        http_method = http_method.upper()
        
        if http_method == method:
            parameters = method_data.get("parameters", [])
            for parameter in parameters:
                paramenter_type = parameter['in']
                if paramenter_type == 'path':
                    if 'path_parameters' not in result:
                        result['path_parameters'] = []
                    result['path_parameters'].append(openapi_parameter_to_parameter_type(parameter))
                elif paramenter_type == 'query':
                    if 'query_parameters' not in result:
                        result['query_parameters'] = []
                    result['query_parameters'].append(openapi_parameter_to_parameter_type(parameter))
                elif paramenter_type == 'header':
                    if 'header_parameters' not in result:
                        result['header_parameters'] = []
                    result['header_parameters'].append(openapi_parameter_to_parameter_type(parameter))
                elif paramenter_type == 'cookie':
                    if 'cookie_parameters' not in result:
                        result['cookie_parameters'] = []
                    result['cookie_parameters'].append(openapi_parameter_to_parameter_type(parameter))
                    
            request_body = method_data.get("requestBody", {})
            if request_body:
                content = request_body['content']
                for content_type, content_data in content.items():
                    if content_type == 'application/json':
                        schema = content_data['schema']
                        properties = schema['properties']
                        for property_name, property_data in properties.items():
                            result.body_parameters.append(ParameterType(name=property_name, type=property_data['type'], description=property_data.get('description', ''), required=property_data.get('required', True)))
    return APIConfiguration(**result).dict()
                