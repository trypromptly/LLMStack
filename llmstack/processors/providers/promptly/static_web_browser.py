import base64
import logging
from typing import List, Optional

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from google.protobuf.json_format import MessageToDict
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.web_browser import (
    BrowserInstruction,
    BrowserInstructionType,
    WebBrowserOutput,
)

logger = logging.getLogger(__name__)


class StaticWebBrowserConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        description="Connection to use",
        widget="connection",
        advanced_parameter=False,
    )
    stream_video: bool = Field(
        description="Stream video of the browser",
        default=False,
    )
    timeout: int = Field(
        description="Timeout in seconds",
        default=10,
        ge=1,
        le=100,
    )


class StaticWebBrowserInput(ApiProcessorSchema):
    url: str = Field(
        description="URL to visit",
    )
    instructions: List[BrowserInstruction] = Field(
        ...,
        description="Instructions to execute",
    )


class StaticWebBrowser(
    ApiProcessorInterface[StaticWebBrowserInput, WebBrowserOutput, StaticWebBrowserConfiguration],
):
    """
    Browse a given URL
    """

    @staticmethod
    def name() -> str:
        return "Static Web Browser"

    @staticmethod
    def slug() -> str:
        return "static_web_browser"

    @staticmethod
    def description() -> str:
        return "Visit a URL and perform actions. Copy, Wait, Goto and Click are the valid instruction types"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""![video](data:videostream/output._video)

{{text}}
""",
        )

    def _request_iterator(
        self,
    ) -> Optional[runner_pb2.PlaywrightBrowserRequest]:
        playwright_request = runner_pb2.PlaywrightBrowserRequest()
        for instruction in self._input.instructions:
            if instruction.type == BrowserInstructionType.GOTO:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.GOTO,
                    data=instruction.data,
                )
            if instruction.type == BrowserInstructionType.CLICK:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.CLICK,
                    selector=instruction.selector,
                )
            elif instruction.type == BrowserInstructionType.WAIT:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.WAIT,
                    selector=instruction.selector,
                )
            elif instruction.type == BrowserInstructionType.COPY:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.COPY,
                    selector=instruction.selector,
                )
            elif instruction.type == BrowserInstructionType.SCROLLX:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.SCROLL_X,
                    selector=instruction.selector,
                    data=instruction.data,
                )
            elif instruction.type == BrowserInstructionType.SCROLLY:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.SCROLL_Y,
                    selector=instruction.selector,
                    data=instruction.data,
                )
            elif instruction.type == BrowserInstructionType.TERMINATE:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.TERMINATE,
                )
            elif instruction.type == BrowserInstructionType.ENTER:
                input = runner_pb2.BrowserInput(
                    type=runner_pb2.ENTER,
                )
            playwright_request.steps.append(input)
        playwright_request.url = self._input.url
        playwright_request.timeout = (
            self._config.timeout
            if self._config.timeout and self._config.timeout > 0 and self._config.timeout <= 100
            else 100
        )
        playwright_request.session_data = (
            self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
            if self._config.connection_id
            else ""
        )
        playwright_request.stream_video = self._config.stream_video

        yield playwright_request

    def process(self) -> dict:
        output_stream = self._output_stream
        output_text = ""
        browser_response = None

        channel = grpc.insecure_channel(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
        )
        stub = runner_pb2_grpc.RunnerStub(channel)

        try:
            playwright_response_iter = stub.GetPlaywrightBrowser(
                self._request_iterator(),
            )
            for response in playwright_response_iter:
                if response.content:
                    response_content = MessageToDict(response.content)
                    if response_content:
                        browser_response = response_content

                if response.state == runner_pb2.TERMINATED or response.content.text:
                    output_text = "".join([x.text for x in response.outputs])
                    if not output_text:
                        output_text = response.content.text
                    break

                if response.video:
                    # Send base64 encoded video
                    async_to_sync(
                        output_stream.write,
                    )(
                        WebBrowserOutput(
                            text="",
                            video=f"data:videostream;name=browser;base64,{base64.b64encode(response.video).decode('utf-8')}",
                        ),
                    )
        except Exception as e:
            logger.exception(e)

        async_to_sync(output_stream.write)(
            WebBrowserOutput(
                text=output_text,
                content=browser_response,
            ),
        )
        output = output_stream.finalize()

        channel.close()

        return output
