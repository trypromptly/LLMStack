import logging
from typing import Optional

from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.web_browser import BrowserRemoteSessionData

logger = logging.getLogger(__name__)


def open_linkedin_profile_page(web_browser, profile_url):
    browser_response = web_browser.run_commands(
        commands=[
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=profile_url,
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.profile-action-compose-option",
                data="2000",
            ),
        ]
    )
    return browser_response


def click_message_button_if_exists(web_browser, profile_page_html):
    soup = BeautifulSoup(profile_page_html, "html.parser")
    browser_response = None
    compose_action_buttons = soup.select("div.profile-action-compose-option button")
    if compose_action_buttons:
        # filter compose_action_buttons on aria-label
        compose_action_buttons = [
            button for button in compose_action_buttons if button.get("aria-label").startswith("Message")
        ]
        button_selectors = [
            f'div.profile-action-compose-option button#{button.get("id")}' for button in compose_action_buttons
        ]
        if button_selectors:
            for button_selector in button_selectors:
                browser_response = web_browser.run_commands(
                    commands=[
                        WebBrowserCommand(
                            command_type=WebBrowserCommandType.CLICK,
                            selector=button_selector,
                        )
                    ]
                )

    return browser_response


def send_message_in_message_box(web_browser, message, profile_page_html):
    soup = BeautifulSoup(profile_page_html, "html.parser")
    browser_response = None
    msg_form = soup.select("div.msg-form__contenteditable")
    if msg_form:
        browser_response = web_browser.run_commands(
            commands=[
                WebBrowserCommand(
                    command_type=WebBrowserCommandType.TYPE,
                    selector="div.msg-form__contenteditable",
                    data=message,
                ),
                WebBrowserCommand(
                    command_type=WebBrowserCommandType.WAIT,
                    selector="button.msg-form__send-button",
                    data="2000",
                ),
                WebBrowserCommand(
                    command_type=WebBrowserCommandType.CLICK,
                    selector="button.msg-form__send-button",
                ),
            ]
        )

    return browser_response


class MessageSenderInput(ApiProcessorSchema):
    profile_url: str = Field(description="The profile URL", default="")
    message: str = Field(description="The message to send", default="")


class MessageSenderOutput(ApiProcessorSchema):
    code: Optional[int] = Field(description="Status code of the message send", default=None)
    session: Optional[BrowserRemoteSessionData] = Field(
        default=None,
        description="Session data from the browser",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if something went wrong",
    )


class MessageSenderConfiguration(ApiProcessorSchema):
    connection_id: str = Field(
        description="LinkedIn login session connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    stream_video: bool = Field(
        description="Stream video of the browser",
        default=False,
    )


class MessageSenderProcessor(
    ApiProcessorInterface[MessageSenderInput, MessageSenderOutput, MessageSenderConfiguration]
):
    @staticmethod
    def name() -> str:
        return "Message Sender"

    @staticmethod
    def slug() -> str:
        return "message_sender"

    @staticmethod
    def description() -> str:
        return "Sends a linkedIn message to a profile."

    @staticmethod
    def provider_slug() -> str:
        return "linkedin"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""<promptly-web-browser-embed wsUrl="{{session.ws_url}}"></promptly-web-browser-embed>"""
        )

    def process(self) -> dict:
        from django.conf import settings

        with WebBrowser(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=self._config.stream_video,
            capture_screenshot=False,
            html=True,
            session_data=(
                self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                if self._config.connection_id
                else ""
            ),
        ) as web_browser:
            if self._config.stream_video and web_browser.get_wss_url():
                async_to_sync(
                    self._output_stream.write,
                )(
                    MessageSenderOutput(
                        session=BrowserRemoteSessionData(
                            ws_url=web_browser.get_wss_url(),
                        ),
                    ),
                )
            browser_response = open_linkedin_profile_page(web_browser, self._input.profile_url)
            if browser_response is None:
                logger.error("Error opening the profile page")
                logger.error(browser_response.command_errors)
                self._output_stream.write(
                    MessageSenderOutput(
                        error="Error opening the profile page",
                    )
                )
                return self._output_stream.finalize()

            browser_response = click_message_button_if_exists(web_browser, browser_response.html)
            if browser_response is None:
                logger.error("Error clicking the message button")
                self._output_stream.write(
                    MessageSenderOutput(
                        error="Error clicking the message button",
                    )
                )
                return self._output_stream.finalize()

            # wait for the message box to load
            browser_response = web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.WAIT,
                        selector="div.msg-form__contenteditable",
                        data="2500",
                    ),
                ]
            )

            browser_response = send_message_in_message_box(web_browser, self._input.message, browser_response.html)
            if browser_response is None:
                logger.error("Error sending the message in the message box")
                self._output_stream.write(
                    MessageSenderOutput(
                        error="Error entering the message in the message box",
                    )
                )
                return self._output_stream.finalize()

        output = self._output_stream.finalize()
        return output
