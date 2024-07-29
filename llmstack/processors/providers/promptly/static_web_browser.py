import logging
import uuid
from typing import List, Optional

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from google.protobuf.json_format import MessageToDict
from langrocks.common.models import tools_pb2, tools_pb2_grpc
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.web_browser import (
    BrowserInstruction,
    BrowserInstructionType,
    BrowserRemoteSessionData,
    WebBrowserOutput,
)

logger = logging.getLogger(__name__)


class StaticWebBrowserConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        default=None,
        description="Connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
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
    skip_tags: bool = Field(
        description="Skip extracting tags. This will skip processing HTML tags and only return text content to speed up processing",
        default=True,
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
            markdown="""
<promptly-web-browser-embed wsUrl="{{session.ws_url}}"></promptly-web-browser-embed>
<pa-asset url="{{content.screenshot}}" type="image/png"></pa-asset>
{{text}}
""",
        )

    def _request_iterator(
        self,
    ) -> Optional[tools_pb2.WebBrowserRequest]:
        playwright_request = tools_pb2.WebBrowserRequest()
        for instruction in self._input.instructions:
            if instruction.type == BrowserInstructionType.GOTO:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.GOTO,
                    data=instruction.data,
                )
            if instruction.type == BrowserInstructionType.CLICK:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.CLICK,
                    selector=instruction.selector,
                )
            elif instruction.type == BrowserInstructionType.WAIT:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.WAIT,
                    selector=instruction.selector,
                )
            elif instruction.type == BrowserInstructionType.COPY:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.COPY,
                    selector=instruction.selector,
                )
            elif instruction.type == BrowserInstructionType.SCROLLX:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.SCROLL_X,
                    selector=instruction.selector,
                    data=instruction.data,
                )
            elif instruction.type == BrowserInstructionType.SCROLLY:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.SCROLL_Y,
                    selector=instruction.selector,
                    data=instruction.data,
                )
            elif instruction.type == BrowserInstructionType.TERMINATE:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.TERMINATE,
                )
            elif instruction.type == BrowserInstructionType.ENTER:
                input = tools_pb2.WebBrowserInput(
                    type=tools_pb2.ENTER,
                )
            playwright_request.inputs.append(input)

        playwright_request.session_config.CopyFrom(
            tools_pb2.WebBrowserSessionConfig(
                init_url=self._input.url,
                skip_tags=self._config.skip_tags,
                timeout=(
                    self._config.timeout
                    if self._config.timeout and self._config.timeout > 0 and self._config.timeout <= 100
                    else 100
                ),
                session_data=(
                    self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                    if self._config.connection_id
                    else ""
                ),
                interactive=self._config.stream_video,
            )
        )

        yield playwright_request

    def process(self) -> dict:
        output_stream = self._output_stream
        output_text = ""
        browser_response = None

        channel = grpc.insecure_channel(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
        )
        stub = tools_pb2_grpc.ToolsStub(channel)

        try:
            web_browser_response_iter = stub.GetWebBrowser(
                self._request_iterator(),
            )
            for response in web_browser_response_iter:
                if response.session and response.session.ws_url:
                    # Send session info to the client
                    async_to_sync(
                        output_stream.write,
                    )(
                        WebBrowserOutput(
                            session=BrowserRemoteSessionData(
                                ws_url=response.session.ws_url,
                            ),
                        ),
                    )
                if response.output:
                    response_content = MessageToDict(response.output)
                    if response_content:
                        browser_response = response_content

                if response.state == tools_pb2.TERMINATED or response.output.text:
                    output_text = "".join([x.output for x in response.output.outputs])
                    if not output_text:
                        output_text = response.content.text
                    break

        except Exception as e:
            logger.exception(e)

        # If browser_response contains screenshot, convert it to objref
        if browser_response and "screenshot" in browser_response:
            screenshot_asset = self._upload_asset_from_url(
                f"data:image/png;name={str(uuid.uuid4())};base64,{browser_response['screenshot']}",
                mime_type="image/png",
            )
            browser_response["screenshot"] = screenshot_asset.objref

        async_to_sync(output_stream.write)(
            WebBrowserOutput(
                text=output_text,
                content=browser_response,
            ),
        )
        output = output_stream.finalize()

        channel.close()

        return output
