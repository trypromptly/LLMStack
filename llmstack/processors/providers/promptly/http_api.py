import logging
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.blocks.http import HttpAPIProcessor as CoreHttpAPIProcessor, HttpAPIProcessorConfiguration, HttpAPIProcessorInput, HttpAPIProcessorOutput
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class PromptlyHttpAPIProcessorInput(HttpAPIProcessorInput, ApiProcessorSchema):
    pass


class PromptlyHttpAPIProcessorOutput(HttpAPIProcessorOutput, ApiProcessorSchema):
    content: Optional[bytes] = Field(widget='hidden')


class PromptlyHttpAPIProcessorConfiguration(HttpAPIProcessorConfiguration, ApiProcessorSchema):
    timeout: Optional[int] = Field(
        description='Timeout in seconds', default=5, example=10, advanced_parameter=False, ge=0, le=60,
    )


class PromptlyHttpAPIProcessor(ApiProcessorInterface[PromptlyHttpAPIProcessorInput, PromptlyHttpAPIProcessorOutput, PromptlyHttpAPIProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'HTTP API Processor'
    
    @staticmethod
    def slug() -> str:
        return 'http_api_processor'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def session_data_to_persist(self) -> dict:
        return {}

    def process(self) -> PromptlyHttpAPIProcessorOutput:
        request = HttpAPIProcessorInput(
            url=self._input.url, method=self._input.method, headers=self._input.headers or {}, body=self._input.body, authorization=self._input.authorization,
        )
        response = CoreHttpAPIProcessor(
            PromptlyHttpAPIProcessorConfiguration(
                allow_redirects=self._config.allow_redirects, timeout=self._config.timeout).dict(),
        ).process(request.dict())

        async_to_sync(self._output_stream.write)(
            PromptlyHttpAPIProcessorOutput(
                code=200, text=response.text, content_json=response.content_json, is_ok=response.is_ok, headers=response.headers,
            ),
        )
        output = self._output_stream.finalize()
        return output
