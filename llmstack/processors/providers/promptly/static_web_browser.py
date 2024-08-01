import base64
import logging
import uuid
from typing import Iterator, List, Optional

from asgiref.sync import async_to_sync
from django.conf import settings
from langrocks.client.web_browser import WebBrowserContextManager
from langrocks.common.models.web_browser import (
    WebBrowserCommand,
    WebBrowserCommandType,
    WebBrowserSessionConfig,
)
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
    ) -> Iterator[WebBrowserCommand]:
        for instruction in self._input.instructions:
            instruction_type = instruction.type
            if instruction.type == BrowserInstructionType.GOTO.value:
                instruction_type = WebBrowserCommandType.GOTO
            elif instruction.type == BrowserInstructionType.CLICK.value:
                instruction_type = WebBrowserCommandType.CLICK
            elif instruction.type == BrowserInstructionType.WAIT.value:
                instruction_type = WebBrowserCommandType.WAIT
            elif instruction.type == BrowserInstructionType.COPY.value:
                instruction_type = WebBrowserCommandType.COPY
            elif instruction.type == BrowserInstructionType.SCROLLX.value:
                instruction_type = WebBrowserCommandType.SCROLL_X
            elif instruction.type == BrowserInstructionType.SCROLLY.value:
                instruction_type = WebBrowserCommandType.SCROLL_Y
            elif instruction.type == BrowserInstructionType.TERMINATE.value:
                instruction_type = WebBrowserCommandType.TERMINATE
            elif instruction.type == BrowserInstructionType.ENTER.value:
                instruction_type = WebBrowserCommandType.ENTER

            yield WebBrowserCommand(
                command_type=instruction_type, data=(instruction.data or ""), selector=(instruction.selector or "")
            )

    def process(self) -> dict:
        output_stream = self._output_stream
        browser_response = None

        with WebBrowserContextManager(f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}") as web_browser:
            session, content_iter = web_browser.run_commands_interactive(
                commands_iterator=self._request_iterator(),
                config=WebBrowserSessionConfig(
                    init_url=self._input.url,
                    timeout=self._config.timeout,
                    interactive=self._config.stream_video,
                    capture_screenshot=True,
                ),
            )

            if session and session.ws_url:
                # Send session info to the client
                async_to_sync(
                    output_stream.write,
                )(
                    WebBrowserOutput(
                        session=BrowserRemoteSessionData(
                            ws_url=session.ws_url,
                        ),
                    ),
                )

            for content in content_iter:
                browser_response = content
        # If browser_response contains screenshot, convert it to objref
        screenshot_asset = None
        if browser_response and browser_response.screenshot:
            screenshot_asset = self._upload_asset_from_url(
                f"data:image/png;name={str(uuid.uuid4())};base64,{base64.b64encode(browser_response.screenshot).decode('utf-8')}",
                mime_type="image/png",
            )

        browser_response = browser_response.model_dump()
        browser_response["screenshot"] = screenshot_asset.objref if screenshot_asset else None

        async_to_sync(output_stream.write)(
            WebBrowserOutput(
                text=browser_response.get(
                    "text",
                    "".join(list(map(lambda x: x.get("output", ""), browser_response.get("command_outputs", [])))),
                ),
                content=browser_response,
            ),
        )
        output = output_stream.finalize()

        return output
