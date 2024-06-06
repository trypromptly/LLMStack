import base64
import logging
from typing import Annotated, List, Literal, Optional, Union

import requests
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.anthropic.messages import (
    MessagesConfiguration,
    MessagesOutput,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


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


class MessagesVisionInput(ApiProcessorSchema):
    messages: List[Message] = Field(
        default=[],
        description="A list of messages, each with a role and message text.",
    )


class MessagesVisionProcessor(ApiProcessorInterface[MessagesVisionInput, MessagesOutput, MessagesConfiguration]):
    @staticmethod
    def name() -> str:
        return "Messages with Vision"

    @staticmethod
    def slug() -> str:
        return "messages_vision"

    @staticmethod
    def description() -> str:
        return "Takes a series of messages as input, and return a model-generated message as output"

    @staticmethod
    def provider_slug() -> str:
        return "anthropic"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{message}}""",
        )

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history:
            return {"chat_history": self._chat_history}

    def process(self) -> MessagesOutput:
        from llmstack.common.utils.sslr import LLM

        client = LLM(provider="anthropic", anthropic_api_key=self._env.get("anthropic_api_key"))
        messages = []

        if self._config.system_prompt:
            messages.append({"role": "system", "content": self._config.system_message})

        if self._chat_history:
            for message in self._chat_history:
                messages.append({"role": message["role"], "content": message["message"]})

        for msg in self._input.messages:
            if msg.type == "image_url":
                asset_uri = self._get_session_asset_data_uri(msg.image_url, include_name=False)
                if asset_uri and asset_uri.startswith("data:"):
                    data_uri = asset_uri
                else:
                    asset_response = requests.get(asset_uri)
                    mime_type = asset_response.headers.get("content-type", "image/png")
                    data_uri = f"data:{mime_type};base64,{base64.b64encode(asset_response.content).decode('utf-8')}"
                msg.image_url = data_uri

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
                mime_type = msg.image_url.split(",")[0].split(":")[1].split(";")[0]
                data = msg.image_url.split(",")[1]
                input_messages.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": data,
                        },
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": input_messages,
            },
        )

        response = client.chat.completions.create(
            messages=messages,
            model=self._config.model.model_name(),
            max_tokens=self._config.max_tokens,
            stream=True,
            temperature=self._config.temperature,
        )

        for result in response:
            choice = result.choices[0]
            if choice.delta.content:
                text_content = "".join(
                    list(map(lambda entry: entry["data"] if entry["type"] == "text" else "", choice.delta.content))
                )
                async_to_sync(self._output_stream.write)(MessagesOutput(message=text_content))
                text_content = ""

        output = self._output_stream.finalize()

        if self._config.retain_history:
            for message in self._input.messages:
                self._chat_history = messages[:]

            self._chat_history.append({"role": "assistant", "message": output.message})

        return output
