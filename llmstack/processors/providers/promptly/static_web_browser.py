import base64
import logging
import uuid
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from django.conf import settings
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import BaseModel, Field, field_validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.web_browser import (
    BrowserRemoteSessionData,
    WebBrowserOutput,
)

logger = logging.getLogger(__name__)


class BrowserInstructionType(str, Enum):
    CLICK = "Click"
    TYPE = "Type"
    WAIT = "Wait"
    GOTO = "Goto"
    COPY = "Copy"
    TERMINATE = "Terminate"
    ENTER = "Enter"
    SCROLLX = "Scrollx"
    SCROLLY = "Scrolly"

    def __str__(self):
        return self.value


class BrowserInstruction(BaseModel):
    type: BrowserInstructionType
    selector: Optional[str] = None
    data: Optional[str] = None

    @field_validator("type")
    def validate_type(cls, v):
        return v.lower().capitalize()


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
    tags_to_extract: List[str] = Field(
        description="Tags to extract. e.g. ['a', 'img']",
        default=[],
        json_schema_extra={"advanced_parameter": True},
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

    def _web_browser_instruction_to_command(self, instruction: BrowserInstruction) -> WebBrowserCommand:
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

        return WebBrowserCommand(
            command_type=instruction_type, data=(instruction.data or ""), selector=(instruction.selector or "")
        )

    def process(self) -> dict:
        output_stream = self._output_stream
        browser_response = None

        with WebBrowser(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=self._config.stream_video,
            capture_screenshot=True,
            tags_to_extract=self._config.tags_to_extract,
            session_data=(
                self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                if self._config.connection_id
                else ""
            ),
        ) as web_browser:
            if self._config.stream_video and web_browser.get_wss_url():
                async_to_sync(
                    output_stream.write,
                )(
                    WebBrowserOutput(
                        session=BrowserRemoteSessionData(
                            ws_url=web_browser.get_wss_url(),
                        ),
                    ),
                )

            browser_response = web_browser.run_commands(
                [
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.GOTO,
                        data=self._input.url,
                    )
                ]
                + list(map(self._web_browser_instruction_to_command, self._input.instructions))
            )

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
