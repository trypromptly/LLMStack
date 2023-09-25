import json
import logging
from pydantic import Field
import requests

from asgiref.sync import async_to_sync

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)

class PromptlyAppProcessorInput(ApiProcessorSchema):
    input: str 

class PromptlyAppProcessorOutput(ApiProcessorSchema):
    output: str

class PromptlyAppProcessorConfiguration(ApiProcessorSchema):
    app_id: str = Field(description='Promptly App Id', advanced_parameter=False, widget='appselect', required=True)
    
class PromptlyAppProcessor(ApiProcessorInterface[PromptlyAppProcessorInput, PromptlyAppProcessorOutput, PromptlyAppProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'promptly/app'

    @staticmethod
    def slug() -> str:
        return 'app'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> dict:
        PROMPTLY_TOKEN = ''
        url = 'http://localhost:8000/api/apps/96b1ed09-f3ea-4195-b681-d90fece6d7cc/run'
        output_stream = self._output_stream
        payload = {
            "input": json.loads(self._input.input),
            "stream": False,
            }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Token " + PROMPTLY_TOKEN,
            }
        response = requests.request("POST", url, headers=headers, json=payload)
        async_to_sync(output_stream.write)(
            PromptlyAppProcessorOutput(output=response.text.encode('utf8')),
        )
        output = output_stream.finalize()
        return output
