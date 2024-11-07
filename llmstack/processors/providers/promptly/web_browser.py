import base64
import logging
import uuid
from typing import List, Literal, Optional, Union

import orjson as json
from asgiref.sync import async_to_sync
from django.conf import settings
from langrocks.client import WebBrowser as WebBrowserClient
from langrocks.common.models.web_browser import (
    WebBrowserCommand,
    WebBrowserCommandType,
    WebBrowserContent,
)
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config
from llmstack.processors.providers.promptly.static_web_browser import (
    BrowserRemoteSessionData,
    StaticWebBrowserDownload,
    StaticWebBrowserFile,
)

logger = logging.getLogger(__name__)


GOTO_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "goto",
        "description": "Navigate to a URL",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Human readable explanation of the action",
                },
                "url": {
                    "type": "string",
                    "description": "URL to navigate to",
                },
            },
            "required": ["explanation", "url"],
        },
    },
}

COPY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "copy",
        "description": "Read text from an element on the page",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Human readable explanation of the action",
                },
                "annotated_tag_id": {
                    "type": "string",
                    "description": "annotated_tag_id to use for the command, if copying body text, use 'body'",
                },
            },
            "required": ["explanation", "annotated_tag_id"],
        },
    },
}

CLICK_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "click",
        "description": "Click on an element based on annotated_tag_id",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Human readable explanation of the action",
                },
                "annotated_tag_id": {
                    "type": "string",
                    "description": "annotated_tag_id to use for the command",
                },
            },
            "required": ["explanation", "annotated_tag_id"],
        },
    },
}

SCROLL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "scroll",
        "description": "Scroll the page",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Human readable explanation of the action",
                },
                "direction": {
                    "enum": ["up", "down", "left", "right"],
                    "type": "string",
                    "description": "Direction to scroll",
                },
            },
            "required": ["explanation", "direction"],
        },
    },
}


TYPE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "enter_text",
        "description": "Type into an input field based on annotated_tag_id",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Human readable explanation of the action",
                },
                "annotated_tag_id": {
                    "type": "string",
                    "description": "annotated_tag_id to use for the command, annotated_tag_id is of form 'in=<number>'",
                },
                "text": {
                    "type": "string",
                    "description": "Text to type",
                },
            },
            "required": ["explanation", "annotated_tag_id", "text"],
        },
    },
}

TERMINATE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "terminate",
        "description": "Terminate the browser session",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Human readable explanation of the action",
                },
            },
            "required": ["explanation"],
        },
    },
}

TOOLS = [
    GOTO_TOOL_SCHEMA,
    COPY_TOOL_SCHEMA,
    CLICK_TOOL_SCHEMA,
    SCROLL_TOOL_SCHEMA,
    TYPE_TOOL_SCHEMA,
    TERMINATE_TOOL_SCHEMA,
]


DEFAULT_SYSTEM_MESSAGE = """You are a browser interaction assistant. Use the provided annotated image to understand the current state of the browser. All the interactive HTML elements on the page are annotated and have a annotated_tag_id associated with each element. Understand the user provided task and generate the required tool instructions to accomplish the task. You have access to the following tools to perform actions in the browser:
- goto: Navigate to a URL
- copy: Read text from an element on the page
- click: Click on an element based on annotated_tag_id
- scroll: Scroll the page
- type: Type into an input field based on annotated_tag_id
- terminate: Terminate the browser session
You need to understand the broser state after each invocations, generate only one tool call at a time. After a user provided task is complete inovke the 'terminate' tool to end the session. Never ask for user input.
"""  # noqa: E501


class Model(StrEnum):
    GPT_3_5_LATEST = "gpt-3.5-turbo-latest"
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_LATEST = "gpt-4-turbo-latest"
    GPT_4_V_LATEST = "gpt-4-vision-latest"
    O1_PREVIEW = "o1-preview"
    O1_MINI = "o1-mini"


class GoogleVisionModel(StrEnum):
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_0_PRO = "gemini-1.0-pro"

    def model_name(self):
        return self.value


class GoogleVisionToolModelConfig(BaseModel):
    provider: Literal["google"] = "google"
    model: GoogleVisionModel = Field(default=GoogleVisionModel.GEMINI_1_5_PRO, description="The model for the LLM")


class OpenAIModel(StrEnum):
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_TURBO_240409 = "gpt-4-turbo-2024-04-09"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"

    def model_name(self):
        return self.value


class OpenAIVisionToolModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.GPT_4_O, description="The model for the LLM")


class AnthropicModel(StrEnum):
    CLAUDE_3_5_Sonnet = "claude-3-5-sonnet"

    def model_name(self):
        if self.value == "claude-3-5-sonnet":
            return "claude-3-5-sonnet-20241022"


class AnthropicVisionToolModelConfig(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    model: AnthropicModel = Field(default=AnthropicModel.CLAUDE_3_5_Sonnet, description="The model for the LLM")


ProviderConfigType = Union[OpenAIVisionToolModelConfig, GoogleVisionToolModelConfig, AnthropicVisionToolModelConfig]


class WebBrowserConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        default=None,
        description="Connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    model: Optional[Model] = Field(
        description="Backing model to use",
        default=Model.GPT_4_O,
        json_schema_extra={"advanced_parameter": False, "widget": "hidden"},
    )
    provider_config: ProviderConfigType = Field(
        default=OpenAIVisionToolModelConfig(),
        json_schema_extra={"advanced_parameter": False, "descrmination_field": "provider"},
    )
    stream_video: bool = Field(
        description="Stream video of the browser",
        default=True,
    )
    stream_text: bool = Field(
        description="Stream output text from the browser",
        default=False,
    )
    timeout: int = Field(
        description="Timeout in seconds",
        default=10,
        ge=1,
        le=100,
    )
    max_steps: int = Field(
        description="Maximum number of browsing steps",
        default=8,
        ge=1,
        le=20,
    )
    system_message: str = Field(
        description="System message to use",
        default=DEFAULT_SYSTEM_MESSAGE,
        json_schema_extra={"widget": "textarea"},
    )
    seed: Optional[int] = Field(
        default=None,
        description="Seed to use for random number generator",
    )
    tags_to_extract: List[str] = Field(
        description="Tags to extract", default=["a", "button", "input", "textarea", "select"]
    )


class WebBrowserOutput(ApiProcessorSchema):
    text: str = Field(default="", description="Text of the result")
    video: Optional[str] = Field(
        default=None,
        description="Video of the result",
    )
    content: Optional[WebBrowserContent] = Field(
        default=None,
        description="Content of the result including text, buttons, links, inputs, textareas and selects",
    )
    session: Optional[BrowserRemoteSessionData] = Field(
        default=None,
        description="Session data from the browser",
    )
    steps: List[str] = Field(
        default=[],
        description="Steps taken to complete the task",
    )


class WebBrowserInput(ApiProcessorSchema):
    start_url: str = Field(
        description="URL to visit to start the session",
        default="https://www.google.com",
    )
    task: str = Field(
        description="Details of the task to perform",
        default="",
    )


class WebBrowser(
    ApiProcessorInterface[WebBrowserInput, WebBrowserOutput, WebBrowserConfiguration],
):
    """
    Browse a given URL
    """

    @staticmethod
    def name() -> str:
        return "Web Browser Agent"

    @staticmethod
    def slug() -> str:
        return "web_browser"

    @staticmethod
    def description() -> str:
        return "Visit a website and perform actions to complete a task"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""<promptly-web-browser-embed wsUrl="{{session.ws_url}}"></promptly-web-browser-embed>
        {{text}}""",
            jsonpath="$.text",
        )

    def _execute_anthropic_instruction_in_browser(
        self, instruction_input, web_browser: WebBrowserClient, prev_browser_state: WebBrowserContent = None
    ):
        if instruction_input.get("action") == "screenshot":
            return web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.SCREENSHOT,
                    )
                ]
            )
        elif instruction_input.get("action") == "mouse_move":
            coordinates = instruction_input.get("coordinate")
            return web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.MOUSE_MOVE,
                        data=json.dumps({"x": coordinates[0], "y": coordinates[1]}),
                    )
                ]
            )
        elif instruction_input.get("action") == "left_click":
            return web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.CLICK,
                    )
                ]
            )
        elif instruction_input.get("action") == "type":
            return web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.TYPE,
                        data=instruction_input.get("text"),
                    )
                ]
            )
        elif instruction_input.get("action") == "key":
            return web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.KEY,
                        data=instruction_input.get("text"),
                    ),
                ]
            )
        else:
            raise Exception("Invalid instruction")

    def _process_anthropic(self) -> dict:
        client = get_llm_client_from_provider_config(
            provider=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.value,
            get_provider_config_fn=self.get_provider_config,
        )
        provider_config = self.get_provider_config(
            provider_slug=self._config.provider_config.provider, model_slug=self._config.provider_config.model.value
        )
        messages = [
            {
                "role": "system",
                "content": f"<SYSTEM_CAPABILITY> You are utilising a virtual chrome browser. If user asks you to visit a website, you can simply start your responses assuming the browser is opened and the current page is {self._input.start_url}.",
            },
            {
                "role": "user",
                "content": f"Perform the following task: {self._input.task}",
            },
        ]
        commands_executed = 0
        browser_response = None
        browser_downloads = []
        with WebBrowserClient(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=self._config.stream_video,
            capture_screenshot=True,
            annotate=False,
            tags_to_extract=self._config.tags_to_extract,
            session_data=(
                self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                if self._config.connection_id
                else ""
            ),
        ) as web_browser:
            browser_response = web_browser.run_commands(
                commands=[
                    WebBrowserCommand(
                        command_type=WebBrowserCommandType.GOTO,
                        data=self._input.start_url,
                    )
                ]
            )
            if browser_response.downloads:
                browser_downloads.extend(browser_response.downloads)
            # Start streaming video if enabled
            if self._config.stream_video and web_browser.get_wss_url():
                async_to_sync(self._output_stream.write)(
                    WebBrowserOutput(
                        session=BrowserRemoteSessionData(ws_url=web_browser.get_wss_url()),
                    ),
                )

            while True:
                if commands_executed > self._config.max_steps:
                    break

                # Trim messages by removing tool call responses with images from all but the last message
                for message in messages[:-1]:
                    if (
                        message.get("role") == "user"
                        and message.get("content")
                        and isinstance(message.get("content"), list)
                        and message.get("content")[0].get("type") == "tool_result"
                    ):
                        message["content"][0]["content"] = []

                response = client.chat.completions.create(
                    model=self._config.provider_config.model.model_name(),
                    messages=messages,
                    seed=self._config.seed,
                    tools=[
                        {
                            "type": "computer_20241022",
                            "name": "computer",
                            "display_width_px": 1024,
                            "display_height_px": 720,
                            "display_number": 1,
                        },
                    ],
                    stream=False,
                    extra_headers={"anthropic-beta": "computer-use-2024-10-22"},
                    max_tokens=4096,
                )
                if response.usage:
                    self._usage_data.append(
                        (
                            f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                            MetricType.INPUT_TOKENS,
                            (provider_config.provider_config_source, response.usage.get_input_tokens()),
                        )
                    )
                    self._usage_data.append(
                        (
                            f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                            MetricType.OUTPUT_TOKENS,
                            (provider_config.provider_config_source, response.usage.get_output_tokens()),
                        )
                    )
                choice = response.choices[0]
                # Append to history of messages
                messages.append(
                    {
                        "role": "assistant",
                        "content": choice.message.content,
                    }
                )
                if choice.finish_reason == "tool_use":
                    tool_responses = []
                    for message_content in choice.message.content:
                        if message_content.get("type") == "tool_use":
                            browser_response = self._execute_anthropic_instruction_in_browser(
                                message_content.get("input", {}),
                                web_browser=web_browser,
                                prev_browser_state=browser_response,
                            )
                            if browser_response.downloads:
                                browser_downloads.extend(browser_response.downloads)
                            command_output = browser_response.command_outputs[0]
                            if message_content.get("input", {}).get("action") == "screenshot":
                                tool_responses.append(
                                    {
                                        "type": "tool_result",
                                        "content": [
                                            {
                                                "type": "image",
                                                "source": {
                                                    "type": "base64",
                                                    "media_type": "image/png",
                                                    "data": command_output.output,
                                                },
                                            },
                                        ],
                                        "tool_use_id": message_content["id"],
                                        "is_error": False,
                                    }
                                )
                            else:
                                tool_responses.append(
                                    {
                                        "type": "tool_result",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": command_output.output,
                                            },
                                        ],
                                        "tool_use_id": message_content["id"],
                                        "is_error": False,
                                    }
                                )
                        else:
                            async_to_sync(self._output_stream.write)(
                                WebBrowserOutput(text=message_content.get("text", "") + "\n\n"),
                            )
                    if tool_responses:
                        messages.append(
                            {
                                "role": "user",
                                "content": tool_responses,
                            }
                        )
                    continue
                elif choice.finish_reason == "end_turn":
                    browser_response = web_browser.run_commands(
                        commands=[
                            WebBrowserCommand(
                                command_type=WebBrowserCommandType.WAIT,
                                data="2",
                            ),
                        ]
                    )
                    if browser_response.downloads:
                        browser_downloads.extend(browser_response.downloads)
                    async_to_sync(self._output_stream.write)(
                        WebBrowserOutput(text=choice.message.content[0].get("text", "")),
                    )
                    break

        if browser_response:
            output_text = "\n".join(list(map(lambda entry: entry.output, browser_response.command_outputs)))
            browser_content = WebBrowserContent(**browser_response.model_dump(exclude=("screenshot", "downloads")))
            screenshot_asset = None
            if browser_response.screenshot:
                screenshot_asset = self._upload_asset_from_url(
                    f"data:image/png;name={str(uuid.uuid4())};base64,{base64.b64encode(browser_response.screenshot).decode('utf-8')}",
                    mime_type="image/png",
                )
            browser_content.screenshot = screenshot_asset.objref if screenshot_asset else None

            if browser_downloads:
                swb_downloads = []
                for download in browser_downloads:
                    # Create an objref for the file data
                    file_data = self._upload_asset_from_url(
                        f"data:{download.file.mime_type};name={download.file.name};base64,{base64.b64encode(download.file.data).decode('utf-8')}",
                        mime_type=download.file.mime_type,
                    )

                    swb_download = StaticWebBrowserDownload(
                        url=download.url,
                        file=StaticWebBrowserFile(
                            name=download.file.name,
                            data=file_data.objref,
                            mime_type=download.file.mime_type,
                        ),
                    )
                    swb_downloads.append(swb_download)
                browser_content.downloads = swb_downloads
            async_to_sync(self._output_stream.write)(WebBrowserOutput(text=output_text, content=browser_content))

        output = self._output_stream.finalize()
        return output

    def process(self) -> dict:
        if self._config.provider_config.provider == "anthropic":
            return self._process_anthropic()

        client = get_llm_client_from_provider_config(
            provider=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.value,
            get_provider_config_fn=self.get_provider_config,
        )
        provider_config = self.get_provider_config(
            provider_slug=self._config.provider_config.provider, model_slug=self._config.provider_config.model.value
        )

        messages = [
            {
                "role": "system",
                "content": self._config.system_message,
            },
            {
                "role": "user",
                "content": f"Perform the following task: {self._input.task}",
            },
        ]
        terminate = False
        with WebBrowserClient(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=self._config.stream_video,
            capture_screenshot=True,
            annotate=True,
            tags_to_extract=self._config.tags_to_extract,
            session_data=(
                self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                if self._config.connection_id
                else ""
            ),
        ) as web_browser:
            # Start streaming video if enabled
            if self._config.stream_video and web_browser.get_wss_url():
                async_to_sync(self._output_stream.write)(
                    WebBrowserOutput(
                        session=BrowserRemoteSessionData(ws_url=web_browser.get_wss_url()),
                    ),
                )
            # First command is to visit the start URL
            commands = [
                WebBrowserCommand(
                    command_type=WebBrowserCommandType.GOTO,
                    data=self._input.start_url,
                ),
            ]
            commands_executed = []
            browser_response = None
            browser_steps = ["Navigate to URL: " + self._input.start_url]
            while commands:
                if len(commands_executed) > self._config.max_steps:
                    break

                browser_response = web_browser.run_commands(commands=commands)
                if browser_response.command_outputs:
                    output_text = "\n".join(list(map(lambda entry: entry.output, browser_response.command_outputs)))
                    async_to_sync(self._output_stream.write)(WebBrowserOutput(text=output_text))

                commands_executed.extend(commands)

                if terminate:
                    commands = []
                    # We executed the final browser instruction, exit the loop
                    break

                page_content = ""
                if browser_response.text:
                    page_content += f"Text on page:\n---\n{browser_response.text}\n---\n"
                if browser_response.links:
                    page_content += "Links on page:\n---\n"
                    for link in browser_response.links:
                        page_content += f"selector: {link.selector}, text: {link.text} url: {link.url}\n"
                    page_content += "---\n"
                if browser_response.buttons:
                    page_content += "Buttons on page:\n---\n"
                    for button in browser_response.buttons:
                        page_content += f"selector: {button.selector}, text: {button.text}\n"
                    page_content += "---\n"
                if browser_response.select_fields:
                    page_content += "\nSelects on page:\n------\n"
                    for select in browser_response.select_fields:
                        page_content += f"selector: {select.selector}, text: {select.text}\n"

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "blob",
                                "mime_type": "image/png",
                                "data": browser_response.screenshot,
                            },
                            {
                                "mime_type": "text/plain",
                                "type": "text",
                                "data": "Page content: " + page_content,
                            },
                        ],
                    }
                )

                response = client.chat.completions.create(
                    model=self._config.provider_config.model.value,
                    messages=messages,
                    seed=self._config.seed,
                    tools=TOOLS,
                    stream=False,
                )
                choice = response.choices[0]
                if choice.message.tool_calls:
                    commands = []
                    if choice.message.tool_calls:
                        # We have new steps to perform remove the browser image from last message
                        messages.pop()
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "mime_type": "text/plain",
                                        "type": "text",
                                        "data": browser_steps[-1],
                                    }
                                ],
                            }
                        )

                    tool_explanation = ""

                    for tool_call in choice.message.tool_calls:
                        messages.append(
                            {
                                "role": "assistant",
                                "content": None,
                                "function_call": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        )

                        args = json.loads(tool_call.function.arguments)
                        tool_explanation += args["explanation"] + "\n"

                        if tool_call.function.name == "goto":
                            commands.append(
                                WebBrowserCommand(
                                    command_type=WebBrowserCommandType.GOTO,
                                    data=args["url"],
                                ),
                            )
                        elif tool_call.function.name == "copy":
                            commands.append(
                                WebBrowserCommand(
                                    command_type=WebBrowserCommandType.COPY,
                                    selector=args["annotated_tag_id"],
                                ),
                            )
                        elif tool_call.function.name == "click":
                            commands.append(
                                WebBrowserCommand(
                                    command_type=WebBrowserCommandType.CLICK,
                                    selector=args["annotated_tag_id"],
                                ),
                            )
                        elif tool_call.function.name == "scroll":
                            commands.append(
                                WebBrowserCommand(
                                    command_type=WebBrowserCommandType.SCROLL_Y,
                                ),
                            )
                        elif tool_call.function.name == "enter_text":
                            commands.append(
                                WebBrowserCommand(
                                    command_type=WebBrowserCommandType.TYPE,
                                    selector=args["annotated_tag_id"],
                                    data=args["text"],
                                ),
                            )
                        elif tool_call.function.name == "terminate":
                            terminate = True

                    if tool_explanation:
                        browser_steps.append(tool_explanation)

                    async_to_sync(self._output_stream.write)(
                        WebBrowserOutput(steps=browser_steps),
                    )
                elif choice.message.content:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": choice.message.content,
                        },
                    )
                    async_to_sync(self._output_stream.write)(
                        WebBrowserOutput(text=choice.message.content),
                    )
                else:
                    break

                if response.usage:
                    self._usage_data.append(
                        (
                            f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                            MetricType.INPUT_TOKENS,
                            (provider_config.provider_config_source, response.usage.get_input_tokens()),
                        )
                    )
                    self._usage_data.append(
                        (
                            f"{self._config.provider_config.provider}/*/{self._config.provider_config.model.model_name()}/*",
                            MetricType.OUTPUT_TOKENS,
                            (provider_config.provider_config_source, response.usage.get_output_tokens()),
                        )
                    )

        if browser_response:
            output_text = "\n".join(list(map(lambda entry: entry.output, browser_response.command_outputs)))
            browser_content = browser_response.model_dump(exclude=("screenshot",))
            screenshot_asset = None
            if browser_response.screenshot:
                screenshot_asset = self._upload_asset_from_url(
                    f"data:image/png;name={str(uuid.uuid4())};base64,{base64.b64encode(browser_response.screenshot).decode('utf-8')}",
                    mime_type="image/png",
                )
            browser_content["screenshot"] = screenshot_asset.objref if screenshot_asset else None
            async_to_sync(self._output_stream.write)(WebBrowserOutput(text=output_text, content=browser_content))

        output = self._output_stream.finalize()
        return output
