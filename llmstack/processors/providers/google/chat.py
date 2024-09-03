import copy
import json
import logging
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

import requests
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class GeminiModel(str, Enum):
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_0_PRO = "gemini-1.0-pro"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class TextMessage(BaseModel):
    type: Literal["text"]

    text: str = Field(
        default="",
        description="The message text.",
    )


class UrlImageMessage(BaseModel):
    type: Literal["image_url"]

    image_url: str = Field(
        default="",
        description="The image data URI.",
    )


Message = Annotated[
    Union[TextMessage, UrlImageMessage],
    Field(json_schema_extra={"discriminator": "type"}),
]


class ToolInput(BaseModel):
    name: str
    description: str
    parameters: Dict


class FunctionCall(ApiProcessorSchema):
    name: str = Field(
        default="",
        description="The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.",
    )
    description: Optional[str] = Field(
        default=None,
        description="The description of what the function does.",
    )
    parameters: Optional[str] = Field(
        title="Parameters",
        json_schema_extra={"widget": "textarea"},
        default=None,
        description="The parameters the functions accepts, described as a JSON Schema object. See the guide for examples, and the JSON Schema reference for documentation about the format.",
    )


class ChatInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default="",
        description="A message from the system, which will be prepended to the chat history.",
        json_schema_extra={"widget": "textarea"},
    )
    messages: List[Message] = Field(
        default=[],
        description="The message text.",
    )
    functions: Optional[List[FunctionCall]] = Field(
        default=None,
        description="A list of functions the model may generate JSON inputs for .",
    )


class SafetySetting(BaseModel):
    category: str
    threshold: str


class GenerationConfig(BaseModel):
    temperature: float = Field(
        le=1.0,
        ge=0.0,
        default=0.5,
        description="The temperature is used for sampling during the response generation.",
    )
    max_output_tokens: int = Field(
        le=8192,
        ge=1,
        default=2048,
        description="Maximum number of tokens that can be generated in the response. A token is approximately four characters. 100 tokens correspond to roughly 60-80 words.",
    )


class ChatConfiguration(ApiProcessorSchema):
    model: GeminiModel = Field(
        description="The model to use for the chat.",
        json_schema_extra={"advanced_parameter": False, "widget": "customselect"},
        default=GeminiModel.GEMINI_1_5_PRO,
    )
    safety_settings: List[SafetySetting]
    generation_config: GenerationConfig = Field(
        json_schema_extra={"advanced_parameter": False},
        default=GenerationConfig(),
    )
    retain_history: bool = Field(
        default=False,
        description="Whether to retain the chat history.",
    )


class Citation(BaseModel):
    startIndex: int
    endIndex: int
    url: str
    title: str
    license: str
    publicationDate: str


class CitationMetadata(BaseModel):
    citations: Optional[List[Citation]] = None


class SafetyAttributes(BaseModel):
    categories: Optional[List[str]] = None
    blocked: bool
    scores: List[float]


class ToolCall(BaseModel):
    id: Optional[str] = None
    """The ID of the tool call."""

    function: Optional[FunctionCall] = None
    """The function that the model called."""

    type: Literal["function"]
    """The type of the tool. Currently, only `function` is supported."""


class ChatOutput(ApiProcessorSchema):
    content: Optional[str] = Field(default=None, description="Generated prediction content.")
    function_calls: Optional[List[ToolCall]] = Field(
        default=None,
    )
    citationMetadata: Optional[CitationMetadata] = Field(
        default=None,
        description="Metadata for the citations found in the response.",
    )
    safetyAttributes: Optional[SafetyAttributes] = Field(
        default=None,
        description="Safety attributes for the response.",
    )


def _convert_schema_dict_to_gapic(schema_dict: Dict[str, Any]):
    """Converts a JsonSchema to a dict that the GAPIC Schema class accepts."""
    gapic_schema_dict = copy.copy(schema_dict)
    if "type" in gapic_schema_dict:
        gapic_schema_dict["type_"] = gapic_schema_dict.pop("type").upper()
    if "format" in gapic_schema_dict:
        gapic_schema_dict["format_"] = gapic_schema_dict.pop("format")
    if "items" in gapic_schema_dict:
        gapic_schema_dict["items"] = _convert_schema_dict_to_gapic(
            gapic_schema_dict["items"],
        )
    properties = gapic_schema_dict.get("properties")
    if properties:
        for property_name, property_schema in properties.items():
            properties[property_name] = _convert_schema_dict_to_gapic(
                property_schema,
            )
    return gapic_schema_dict


class ChatProcessor(
    ApiProcessorInterface[ChatInput, ChatOutput, ChatConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Chat Completions"

    @staticmethod
    def slug() -> str:
        return "chat"

    @staticmethod
    def description() -> str:
        return "Google's Chat Completions with Gemini."

    @staticmethod
    def provider_slug() -> str:
        return "google"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{content}}""",
        )

    def get_image_bytes_mime_type(self, image_url: str):
        response = requests.get(image_url)
        if response.status_code != 200:
            raise ValueError(f"Invalid image URL: {image_url}")
        image_bytes = response.content
        mime_type = response.headers["Content-Type"]
        return image_bytes, mime_type

    def process_session_data(self, session_data):
        self._chat_history = session_data.get("chat_history", [])

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history}

    def process(self) -> dict:
        tools = []
        input_token_usage_data = None
        output_token_usage_data = None

        messages = self._chat_history if self._config.retain_history else []

        if self._input.functions:
            for tool_function in self._input.functions:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool_function.name,
                            "description": tool_function.description,
                            "parameters": json.loads(tool_function.parameters),
                        },
                    }
                )

        if self._input.messages:
            for input_message in self._input.messages:
                if isinstance(input_message, TextMessage):
                    messages.append(
                        {
                            "role": "user",
                            "content": input_message.text,
                        }
                    )
                elif isinstance(input_message, UrlImageMessage):
                    image_url = input_message.image_url

                    if image_url.startswith("data:"):
                        content, mime_type = image_url.split(",", 1)
                    elif image_url.startswith("http"):
                        content, mime_type = self.get_image_bytes_mime_type(image_url)
                    elif image_url.startswith("objref://"):
                        data_uri = self._get_session_asset_data_uri(image_url, include_name=True)
                        mime_type, _, content = validate_parse_data_uri(data_uri)

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "blob",
                                    "data": content,
                                    "mime_type": mime_type,
                                }
                            ],
                        }
                    )

        client = get_llm_client_from_provider_config("google", self._config.model.value, self.get_provider_config)
        provider_config = self.get_provider_config(provider_slug="google", model_slug=self._config.model.value)

        messages_to_send = (
            [
                {
                    "role": "system",
                    "content": self._input.system_message,
                },
            ]
            + messages
            if self._input.system_message
            else messages
        )

        response = client.chat.completions.create(
            messages=messages_to_send,
            tools=tools,
            model=self._config.model.value,
            stream=True,
            n=1,
            max_tokens=self._config.generation_config.max_output_tokens,
            temperature=self._config.generation_config.temperature,
        )

        for result in response:
            if result.usage:
                input_token_usage_data = (
                    f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                    MetricType.INPUT_TOKENS,
                    (provider_config.provider_config_source, result.usage.input_tokens),
                )
                output_token_usage_data = (
                    f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                    MetricType.OUTPUT_TOKENS,
                    (provider_config.provider_config_source, result.usage.output_tokens),
                )

            choice = result.choices[0]
            if choice.delta.content:
                if isinstance(choice.delta.content, str):
                    async_to_sync(self._output_stream.write)(ChatOutput(content=choice.delta.content))
                elif isinstance(choice.delta.content, list):
                    for content in choice.delta.content:
                        if content["type"] == "text":
                            async_to_sync(self._output_stream.write)(ChatOutput(content=content["data"]))
                        elif content["type"] == "tool_call":
                            async_to_sync(self._output_stream.write)(
                                ChatOutput(
                                    function_calls=[
                                        ToolCall(
                                            id=content["id"],
                                            function=FunctionCall(
                                                name=content["tool_name"], parameters=content["tool_args"]
                                            ),
                                            type="function",
                                        )
                                    ]
                                )
                            )

        output = self._output_stream.finalize()
        if input_token_usage_data:
            self._usage_data.append(input_token_usage_data)
        if output_token_usage_data:
            self._usage_data.append(output_token_usage_data)

        # Persist history if requested
        if self._config.retain_history:
            self._chat_history = copy.deepcopy(messages)
            self._chat_history.append({"role": "assistant", "message": output.content})

        return output
