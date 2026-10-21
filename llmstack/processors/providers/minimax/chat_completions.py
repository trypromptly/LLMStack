import logging
from typing import Annotated, List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import Field, model_validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.minimax.client import create_minimax_client

logger = logging.getLogger(__name__)


class MessagesModel(StrEnum):
    MINIMAX_M3_1_FLASH = "MiniMax-M3.1-Flash"
    MINIMAX_M3 = "MiniMax-M3"

    def model_name(self):
        return self.value


class ThinkingType(StrEnum):
    ADAPTIVE = "adaptive"
    DISABLED = "disabled"


class Role(StrEnum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class TextContent(ApiProcessorSchema):
    type: Literal["text"]
    text: str = Field(description="The message text.")


class MediaUrl(ApiProcessorSchema):
    url: str = Field(description="A public URL or data URL.")
    detail: Optional[Literal["low", "default", "high"]] = Field(
        default=None,
        description="The media understanding detail level.",
    )
    max_long_side_pixel: Optional[int] = Field(
        default=None,
        ge=1,
        description="The longest-side pixel limit.",
    )


class VideoUrl(MediaUrl):
    url: str = Field(description="A public URL, data URL, or uploaded file reference.")
    fps: Optional[float] = Field(
        default=None,
        ge=0.2,
        le=5,
        description="The video frame sampling rate.",
    )


class ImageContent(ApiProcessorSchema):
    type: Literal["image_url"]
    image_url: MediaUrl


class VideoContent(ApiProcessorSchema):
    type: Literal["video_url"]
    video_url: VideoUrl


MessageContent = Annotated[
    Union[TextContent, ImageContent, VideoContent],
    Field(discriminator="type"),
]


class ChatMessage(ApiProcessorSchema):
    role: Role = Field(
        default=Role.USER,
        description="The role of the message. Can be 'system', 'user', or 'assistant'.",
    )
    message: Union[str, List[MessageContent]] = Field(
        default="",
        description="Text or multimodal message content. MiniMax-M3.1-Flash and MiniMax-M3 support images and video.",
        json_schema_extra={"widget": "textarea"},
    )


class MessagesInput(ApiProcessorSchema):
    messages: List[ChatMessage] = Field(
        default=[
            ChatMessage(),
        ],
        description="A list of messages, each with a role and message text.",
    )


class MessagesOutput(ApiProcessorSchema):
    result: str = Field(description="The response message.")


class MessagesConfiguration(ApiProcessorSchema):
    system_prompt: str = Field(
        default="",
        description="A system prompt is a way of providing context and instructions to the model.",
        json_schema_extra={"widget": "textarea", "advanced_parameter": False},
    )
    model: str = Field(
        default=MessagesModel.MINIMAX_M3_1_FLASH.value,
        min_length=1,
        description=(
            "The MiniMax model that will generate the responses. MiniMax-M3.1-Flash and MiniMax-M3 have a "
            "1,000,000-token context window. Saved legacy and custom model IDs remain supported."
        ),
        json_schema_extra={
            "advanced_parameter": False,
            "widget": "customselect",
            "options": [model.value for model in MessagesModel],
        },
    )
    max_tokens: int = Field(
        ge=1,
        default=256,
        description="The maximum number of tokens to generate before stopping.",
        json_schema_extra={"advanced_parameter": False},
    )
    temperature: float = Field(
        default=1.0,
        description="Amount of randomness injected into the response.",
        ge=0.0,
        le=2.0,
        json_schema_extra={"advanced_parameter": False},
    )
    thinking: ThinkingType = Field(
        default=ThinkingType.ADAPTIVE,
        description="MiniMax-M3 supports adaptive or disabled thinking. Flash and MiniMax-M2.7 require thinking.",
    )
    reasoning_effort: Literal["low", "medium", "high", "xhigh", "max"] = Field(
        default="max",
        description="Thinking effort for MiniMax-M3.1-Flash. Not sent for other models.",
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
    )

    @model_validator(mode="after")
    def validate_model_options(self):
        if self.model in (MessagesModel.MINIMAX_M3_1_FLASH, "MiniMax-M2.7") and self.thinking == ThinkingType.DISABLED:
            raise ValueError(f"{self.model} does not support disabling thinking")
        max_output_tokens = {
            MessagesModel.MINIMAX_M3_1_FLASH: 524288,
            MessagesModel.MINIMAX_M3: 524288,
            "MiniMax-M2.7": 204800,
        }.get(self.model)
        if max_output_tokens is not None and self.max_tokens > max_output_tokens:
            raise ValueError(f"{self.model} supports at most {max_output_tokens} output tokens")
        return self


class MessagesProcessor(ApiProcessorInterface[MessagesInput, MessagesOutput, MessagesConfiguration]):
    @staticmethod
    def name() -> str:
        return "Chat Completions"

    @staticmethod
    def slug() -> str:
        return "chat_completions"

    @staticmethod
    def description() -> str:
        return "MiniMax Chat Completions"

    @staticmethod
    def provider_slug() -> str:
        return "minimax"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{{ result }}""",
            jsonpath="$.result",
        )

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history:
            return {"chat_history": self._chat_history}
        return {}

    def process(self) -> MessagesOutput:
        messages = []

        if self._config.system_prompt:
            messages.append({"role": "system", "content": self._config.system_prompt})

        if self._chat_history:
            for message in self._chat_history:
                messages.append({"role": message["role"], "content": message["message"]})

        for message in self._input.messages:
            if isinstance(message.message, list):
                content = [part.model_dump(exclude_none=True) for part in message.message]
            else:
                content = message.message
            messages.append({"role": str(message.role), "content": content})

        has_media = any(
            isinstance(message["content"], list)
            and any(
                isinstance(part, dict) and part.get("type") in ("image_url", "video_url") for part in message["content"]
            )
            for message in messages
        )
        if self._config.model == "MiniMax-M2.7" and has_media:
            raise ValueError("MiniMax-M2.7 only supports text input")

        minimax_provider_config = self.get_provider_config(model_slug=self._config.model)
        client = create_minimax_client(minimax_provider_config)
        extra_body = {"thinking": {"type": self._config.thinking.value}}
        if self._config.model == MessagesModel.MINIMAX_M3_1_FLASH:
            if minimax_provider_config.base_url.rstrip("/").endswith("/anthropic"):
                extra_body["output_config"] = {"effort": self._config.reasoning_effort}
            else:
                extra_body["reasoning_effort"] = self._config.reasoning_effort

        response = client.chat.completions.create(
            messages=messages,
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            stream=True,
            temperature=self._config.temperature,
            extra_body=extra_body,
        )

        for result in response:
            choice = result.choices[0]
            if choice.delta.content:
                if isinstance(choice.delta.content, list):
                    text_content = "".join(
                        entry.get("data", "") for entry in choice.delta.content if entry.get("type") == "text"
                    )
                else:
                    text_content = choice.delta.content
                if text_content:
                    async_to_sync(self._output_stream.write)(MessagesOutput(result=text_content))

        output = self._output_stream.finalize()

        if self._config.retain_history:
            for message in self._input.messages:
                if isinstance(message.message, list):
                    persisted_message = [part.model_dump(exclude_none=True) for part in message.message]
                else:
                    persisted_message = message.message
                self._chat_history.append({"role": str(message.role), "message": persisted_message})

            self._chat_history.append({"role": "assistant", "message": output.result})

        return output
