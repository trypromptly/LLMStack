import copy
import json
import logging
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

import google.generativeai as genai
import requests
from asgiref.sync import async_to_sync
from google.ai.generativelanguage_v1beta.types import content as gag_content
from google.generativeai.types import content_types
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.google import API_KEY, get_google_credential_from_env

logger = logging.getLogger(__name__)


class GeminiModel(str, Enum):
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

    def __str__(self):
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
    Field(discriminator="type"),
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
        widget="textarea",
        default=None,
        description="The parameters the functions accepts, described as a JSON Schema object. See the guide for examples, and the JSON Schema reference for documentation about the format.",
    )


class ChatInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default="",
        description="A message from the system, which will be prepended to the chat history.",
        widget="textarea",
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
        advanced_parameter=False,
        default=GeminiModel.GEMINI_PRO,
    )
    safety_settings: List[SafetySetting]
    generation_config: GenerationConfig = Field(
        advanced_parameter=False,
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
    citations: Optional[List[Citation]]


class SafetyAttributes(BaseModel):
    categories: Optional[List[str]]
    blocked: bool
    scores: List[float]


class ToolCall(BaseModel):
    id: Optional[str]
    """The ID of the tool call."""

    function: Optional[FunctionCall]
    """The function that the model called."""

    type: Literal["function"]
    """The type of the tool. Currently, only `function` is supported."""


class ChatOutput(ApiProcessorSchema):
    content: Optional[str] = Field(description="Generated prediction content.")
    function_calls: Optional[List[ToolCall]] = Field()
    citationMetadata: Optional[CitationMetadata] = Field(
        description="Metadata for the citations found in the response.",
    )
    safetyAttributes: Optional[SafetyAttributes] = Field(
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
        return "Gemini"

    @staticmethod
    def slug() -> str:
        return "chat"

    @staticmethod
    def description() -> str:
        return "Google generative model"

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
        history = self._chat_history if self._config.retain_history else []

        token, token_type = get_google_credential_from_env(self._env)
        if token_type != API_KEY:
            raise ValueError("Invalid token type. Gemini needs an API key.")

        genai.configure(api_key=token)

        messages = []
        # Add history to messages
        for message in history:
            messages.append(message)

        # Add system message to message_params
        message_params = (
            [
                {"text": self._input.system_message},
            ]
            if self._input.system_message
            else []
        )

        if self._config.model.value == GeminiModel.GEMINI_PRO:
            for message in self._input.messages:
                if message.type == "image_url":
                    raise ValueError(
                        "Gemini Pro does not support image input.",
                    )
                elif message.type == "text":
                    message_params.append({"text": message.text})

        elif self._config.model.value == GeminiModel.GEMINI_PRO_VISION:
            for message in self._input.messages:
                if message.type == "image_url":
                    image_url = message.image_url
                    if image_url.startswith("data:"):
                        content, mime_type = image_url.split(",", 1)
                    elif image_url.startswith("http"):
                        content, mime_type = self.get_image_bytes_mime_type(
                            image_url,
                        )
                    message_params.append(
                        {
                            "mime_type": mime_type,
                            "data": content,
                        },
                    )
                elif message.type == "text":
                    message_params.append({"text": message.text})
        else:
            raise ValueError(f"Invalid model: {self._config.model.value}")

        # Add current user provided input to messages
        messages.append({"parts": message_params, "role": "user"})

        if self._input.functions:
            tools = []
            for function in self._input.functions:
                function_declarations = gag_content.FunctionDeclaration(
                    {
                        "name": function.name,
                        "description": function.description,
                        "parameters": _convert_schema_dict_to_gapic(
                            json.loads(
                                function.parameters,
                            ),
                        ),
                    },
                )

                tools.append(
                    gag_content.Tool(
                        {"function_declarations": [function_declarations]},
                    ),
                )

        else:
            tools = None

        model = genai.GenerativeModel(self._config.model.value, tools=tools)

        # Send it over to the model
        response = model.generate_content(
            contents=content_types.to_contents(messages),
            generation_config={
                "max_output_tokens": self._config.generation_config.max_output_tokens,
                "temperature": self._config.generation_config.temperature,
            },
            stream=True,
        )

        for chunk in response:
            result_text = ""
            function_calls = []
            for part in chunk.parts:
                if part.text:
                    result_text += part.text
                elif part.function_call:
                    function_calls.append(
                        {"name": part.function_call.name, "args": dict(part.function_call.args.items())},
                    )

            tool_calls = list(
                map(
                    lambda x: ToolCall(
                        type="function",
                        function=FunctionCall(
                            name=x["name"],
                            parameters=json.dumps(x["args"]),
                        ),
                    ),
                    function_calls,
                ),
            )

            if len(result_text) > 0:
                async_to_sync(
                    self._output_stream.write,
                )(
                    ChatOutput(
                        content=result_text,
                    ),
                )
            elif len(tool_calls) > 0:
                async_to_sync(
                    self._output_stream.write,
                )(
                    ChatOutput(
                        function_calls=tool_calls,
                    ),
                )

        output = self._output_stream.finalize()

        # Persist history if requested
        if self._config.retain_history:
            history = history + messages + [{"parts": [{"text": output.prediction.content}], "role": "model"}]
            self._chat_history = history

        return output
