import logging
from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from openai import OpenAI
from pydantic import BaseModel, Field, confloat, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.llm.openai import (
    OpenAIChatCompletionsAPIProcessorConfiguration,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    def __str__(self):
        return self.value


class ChatCompletionsVisionModel(str, Enum):
    GPT_4_Vision = "gpt-4-vision-preview"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_TURBO_240409 = "gpt-4-turbo-2024-04-09"
    GPT_4_1106_VISION_PREVIEW = "gpt-4-1106-vision-preview"
    GPT_4_O = "gpt-4o"

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


class ChatMessage(ApiProcessorSchema):
    role: Optional[Role] = Field(
        default=Role.USER,
        description="The role of the message sender. Can be 'user' or 'assistant' or 'system'.",
    )
    content: List[Union[TextMessage, UrlImageMessage]] = Field(
        default=[],
        description="The message text.",
    )


class ChatCompletionsVisionInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default="",
        description="A message from the system, which will be prepended to the chat history.",
        widget="textarea",
    )
    messages: List[Message] = Field(
        default=[],
        description="A list of messages, each with a role and message text.",
    )


class ChatCompletionsVisionOutput(ApiProcessorSchema):
    result: str = Field(default="", description="The model-generated message.")


class ChatCompletionsVisionConfiguration(
    OpenAIChatCompletionsAPIProcessorConfiguration,
    ApiProcessorSchema,
):
    model: ChatCompletionsVisionModel = Field(
        default=ChatCompletionsVisionModel.GPT_4_Vision,
        description="ID of the model to use. Currently, only `gpt-4-vision-preview` is supported.",
        advanced_parameter=False,
    )
    max_tokens: Optional[conint(ge=1, le=32000)] = Field(
        1024,
        description="The maximum number of tokens allowed for the generated answer. By default, the number of tokens the model can return will be (4096 - prompt tokens).\n",
        example=1024,
        advanced_parameter=False,
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n",
        example=1,
        advanced_parameter=False,
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
        advanced_parameter=False,
    )

    auto_prune_chat_history: Optional[bool] = Field(
        default=False,
        description="Automatically prune chat history. This is only applicable if 'retain_history' is set to 'true'.",
    )


class ChatCompletionsVision(
    ApiProcessorInterface[ChatCompletionsVisionInput, ChatCompletionsVisionOutput, ChatCompletionsVisionConfiguration],
):
    """
    OpenAI Chat Completions with vision API
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    @staticmethod
    def name() -> str:
        return "ChatGPT with Vision"

    @staticmethod
    def slug() -> str:
        return "chatgpt_vision"

    @staticmethod
    def description() -> str:
        return "Takes a series of messages as input, and return a model-generated message as output"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{result}}""",
        )

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history}

    def process(self) -> dict:
        output_stream = self._output_stream

        chat_history = self._chat_history if self._config.retain_history else []
        messages = []
        messages.append(
            {"role": "system", "content": self._input.system_message},
        )

        for msg in chat_history:
            messages.append(msg)

        # If message is a UrlImageMessage, check if it has objref and convert it to a data URI
        for msg in self._input.messages:
            if msg.type == "image_url":
                # Convert objref to data URI if it exists
                msg.image_url = self._get_session_asset_data_uri(msg.image_url, include_name=False)

        if self._config.model == ChatCompletionsVisionModel.GPT_4_Vision:
            messages.append(
                {
                    "role": "user",
                    "content": [msg.dict() for msg in self._input.messages],
                },
            )
        else:
            input_messages = []
            for msg in self._input.messages:
                if isinstance(msg, TextMessage):
                    input_messages.append(
                        {
                            "type": "text",
                            "text": msg.text,
                        }
                    )
                elif isinstance(msg, UrlImageMessage):
                    input_messages.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": msg.image_url,
                            },
                        }
                    )
            messages.append(
                {
                    "role": "user",
                    "content": input_messages,
                },
            )

        openai_client = OpenAI(api_key=self._env["openai_api_key"])
        result = openai_client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            temperature=self._config.temperature,
            stream=True,
            max_tokens=self._config.max_tokens,
        )

        for data in result:
            if (
                data.object == "chat.completion.chunk"
                and len(
                    data.choices,
                )
                > 0
                and data.choices[0].delta
                and data.choices[0].delta.content
            ):
                async_to_sync(output_stream.write)(
                    ChatCompletionsVisionOutput(
                        result=data.choices[0].delta.content,
                    ),
                )

        output = self._output_stream.finalize()

        # Update chat history
        for message in self._input.messages:
            self._chat_history.append(message)
        self._chat_history.append(
            {
                "role": "assistant",
                "content": (
                    output["result"]
                    if isinstance(
                        output,
                        dict,
                    )
                    else output.result
                ),
            },
        )

        return output
