import base64
import logging
from enum import Enum
from typing import List, Optional

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic import BaseModel, Field, validator

from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class WebBrowserConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        description='Connection to use', widget='connectionselect', advanced_parameter=False)
    stream_video: bool = Field(
        description='Stream video of the browser', default=False)
    timeout: int = Field(
        description='Timeout in seconds', default=10, ge=1, le=100)


class BrowserInstructionType(str, Enum):
    CLICK = 'Click'
    TYPE = 'Type'
    WAIT = 'Wait'
    GOTO = 'Goto'
    COPY = 'Copy'

    def __str__(self):
        return self.value


class BrowserInstruction(BaseModel):
    type: BrowserInstructionType
    selector: Optional[str] = None
    data: Optional[str] = None

    @validator('type', pre=True, always=True)
    def validate_type(cls, v):
        return v.lower().capitalize()


class WebBrowserInput(ApiProcessorSchema):
    url: str = Field(
        description='URL to visit')
    instructions: List[BrowserInstruction] = Field(
        ..., description='Instructions to execute')


class WebBrowserOutput(ApiProcessorSchema):
    text: str = Field(default='', description='Text of the result')
    video: Optional[str] = Field(
        default=None, description='Video of the result')


class WebBrowser(ApiProcessorInterface[WebBrowserInput, WebBrowserOutput, WebBrowserConfiguration]):
    """
    Browse a given URL
    """
    @staticmethod
    def name() -> str:
        return 'Web Browser'

    @staticmethod
    def slug() -> str:
        return 'web_browser'

    @staticmethod
    def description() -> str:
        return 'Visit a URL and perform actions'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> dict:
        output_stream = self._output_stream
        output_text = ''

        channel = grpc.insecure_channel(
            f'{settings.RUNNER_HOST}:{settings.RUNNER_PORT}')
        stub = runner_pb2_grpc.RunnerStub(channel)

        try:
            playwright_request = runner_pb2.PlaywrightBrowserRequest()
            for instruction in self._input.instructions:
                if instruction.type == BrowserInstructionType.GOTO:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.GOTO, data=instruction.data)
                if instruction.type == BrowserInstructionType.CLICK:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.CLICK, selector=instruction.selector)
                elif instruction.type == BrowserInstructionType.WAIT:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.WAIT, selector=instruction.selector)
                elif instruction.type == BrowserInstructionType.COPY:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.COPY, selector=instruction.selector)
                playwright_request.steps.append(input)
            playwright_request.url = self._input.url
            playwright_request.timeout = self._config.timeout if self._config.timeout and self._config.timeout > 0 and self._config.timeout <= 100 else 100
            playwright_request.session_data = self._env['connections'][self._config.connection_id][
                'configuration']['_storage_state'] if self._config.connection_id else ''
            playwright_request.stream_video = self._config.stream_video

            playwright_response_iter = stub.GetPlaywrightBrowser(
                playwright_request)
            for response in playwright_response_iter:
                if response.state == runner_pb2.TERMINATED:
                    output_text = "".join([x.text for x in response.outputs])
                    break

                if response.video:
                    # Send base64 encoded video
                    async_to_sync(output_stream.write)(WebBrowserOutput(
                        text='',
                        video=f"data:videostream;name=browser;base64,{base64.b64encode(response.video).decode('utf-8')}"
                    ))

        except Exception as e:
            logger.exception(e)

        async_to_sync(output_stream.write)(WebBrowserOutput(
            text=output_text
        ))
        output = output_stream.finalize()

        channel.close()

        return output
