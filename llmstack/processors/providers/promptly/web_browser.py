import base64
import logging
import uuid
from enum import Enum
from typing import List, Literal, Optional, Union

import orjson as json
from asgiref.sync import async_to_sync
from django.conf import settings
from langrocks.client import WebBrowser as WebBrowserClient
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

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


class Model(str, Enum):
    GPT_3_5_LATEST = "gpt-3.5-turbo-latest"
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_LATEST = "gpt-4-turbo-latest"
    GPT_4_V_LATEST = "gpt-4-vision-latest"

    def __str__(self):
        return self.value


class GoogleVisionModel(str, Enum):
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_0_PRO = "gemini-1.0-pro"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class GoogleVisionToolModelConfig(BaseModel):
    provider: Literal["google"] = "google"
    model: GoogleVisionModel = Field(default=GoogleVisionModel.GEMINI_1_5_PRO, description="The model for the LLM")


class OpenAIModel(str, Enum):
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_TURBO_240409 = "gpt-4-turbo-2024-04-09"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class OpenAIVisionToolModelConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model: OpenAIModel = Field(default=OpenAIModel.GPT_4_O, description="The model for the LLM")


ProviderConfigType = Union[OpenAIVisionToolModelConfig, GoogleVisionToolModelConfig]


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


class BrowserRemoteSessionData(BaseModel):
    ws_url: str = Field(
        description="Websocket URL to connect to",
    )


class WebBrowserOutput(ApiProcessorSchema):
    text: str = Field(default="", description="Text of the result")
    video: Optional[str] = Field(
        default=None,
        description="Video of the result",
    )
    content: Optional[dict] = Field(
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
        return "Web Browser"

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
        )

    def process(self) -> dict:
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
            model_steps = []
            while commands:
                if len(commands_executed) > self._config.max_steps:
                    break

                browser_response = web_browser.run_commands(commands=commands)
                commands_executed.extend(commands)
                if terminate:
                    commands = []
                    # We executed the final browser instruction, exit the loop
                    break
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "mime_type": "text/plain",
                                "type": "text",
                                "data": "Current page: " + self._input.start_url,
                            },
                            {
                                "type": "blob",
                                "mime_type": "image/png",
                                "data": browser_response.screenshot,
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
                        model_steps.append(args["explanation"])

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

                    async_to_sync(self._output_stream.write)(
                        WebBrowserOutput(steps=model_steps),
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
            browser_content = browser_response.model_dump(exclude=("screenshot",))
            screenshot_asset = None
            if browser_response.screenshot:
                screenshot_asset = self._upload_asset_from_url(
                    f"data:image/png;name={str(uuid.uuid4())};base64,{base64.b64encode(browser_response.screenshot).decode('utf-8')}",
                    mime_type="image/png",
                )
            browser_content["screenshot"] = screenshot_asset.objref if screenshot_asset else None
            async_to_sync(self._output_stream.write)(WebBrowserOutput(content=browser_content))

        output = self._output_stream.finalize()
        return output
