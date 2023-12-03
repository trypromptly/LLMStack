from enum import Enum

import orjson as json
from asgiref.sync import async_to_sync
from jinja2 import Template
from pydantic import Field

from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)


class HTTPMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'

    def __str__(self):
        return self.value


class RestApiInput(ApiProcessorSchema):
    input: str = Field(
        default='{}', description='JSON dictionary of key value pairs to use in the API call', widget='textarea')


class RestApiOutput(ApiProcessorSchema):
    text: str = Field(
        default='', description='Text returned by the API call', widget='textarea')
    json_data: dict = Field(
        default={}, description='JSON returned by the API call', widget='textarea', alias='json')
    code: int = Field(
        default=200, description='HTTP status code returned by the API call')


class RestApiConfiguration(ApiProcessorSchema):
    url: str = Field(
        default='https://api.apollo.io/v1/', description='URL of the API endpoint', advanced_parameter=False)
    method: HTTPMethod = Field(
        default=HTTPMethod.GET, description='HTTP method to use', advanced_parameter=False)
    body: str = Field(
        default='', description='Body of the request in JSON', widget='textarea')
    connection_id: str = Field(
        default='', description='Connection to use for the API call', widget='connection', advanced_parameter=False)


class RestApiProcessor(ApiProcessorInterface[RestApiInput, RestApiOutput, RestApiConfiguration]):
    """
    REST API processor
    """
    @staticmethod
    def name() -> str:
        return 'REST API'

    @staticmethod
    def slug() -> str:
        return 'rest_api'

    @staticmethod
    def description() -> str:
        return 'Call Apollo REST API'

    @staticmethod
    def provider_slug() -> str:
        return 'apollo'

    def process(self) -> dict:
        import requests

        url = self._config.url
        method = self._config.method

        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        }

        # Treat url and body as a templates and replace any variables with values from the input
        url_template = Template(url)
        url = url_template.render(json.loads(self._input.input))

        body_template = Template(self._config.body)
        body = body_template.render(json.loads(self._input.input))

        response = None
        api_key = self._env['connections'][self._config.connection_id]['configuration']['api_key']
        if method == HTTPMethod.GET:
            if '?' in url:
                url += f'&api_key={api_key}'
            else:
                url += f'?api_key={api_key}'
            response = requests.request(
                method, url, headers=headers)
        else:
            body = self._input.input
            try:
                body = json.loads(body)
                body['api_key'] = api_key
            except:
                pass
            response = requests.request(
                method, url, headers=headers, json=body)

        async_to_sync(self._output_stream.write)(RestApiOutput(
            text=response.text, json=response.json(), code=response.status_code))

        return self._output_stream.finalize()
