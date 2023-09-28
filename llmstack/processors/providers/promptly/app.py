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
    app_id: str = Field(description='Promptly App Id',
                        advanced_parameter=False, widget='appselect', required=True)


class PromptlyAppProcessor(ApiProcessorInterface[PromptlyAppProcessorInput, PromptlyAppProcessorOutput, PromptlyAppProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Promptly App'

    @staticmethod
    def slug() -> str:
        return 'app'

    @staticmethod
    def description() -> str:
        return 'Use existing Promptly app as a processor'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> dict:
        PROMPTLY_TOKEN = self._env.get('promptly_token')

        url = f'https://trypromptly.com/api/apps/{self._config.app_id}/run'

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
