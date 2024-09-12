import copy
import logging
from typing import Annotated, List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils import prequests
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.anthropic.messages import (
    MessagesConfiguration,
    MessagesOutput,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

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
    Field(json_schema_extra={"descriminator": "type"}),
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
            jsonpath="$.message",
        )

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history:
            return {"chat_history": self._chat_history}

    def get_image_bytes_mime_type(self, image_url: str):
        response = prequests.get(image_url)
        if response.status_code != 200:
            raise ValueError(f"Invalid image URL: {image_url}")
        image_bytes = response.content
        mime_type = response.headers["Content-Type"]
        return image_bytes, mime_type

    def process(self) -> MessagesOutput:
        messages = self._chat_history if self._config.retain_history else []

        if self._input.messages:
            parts = []
            for input_message in self._input.messages:
                if isinstance(input_message, TextMessage):
                    parts.append(
                        {
                            "mime_type": "text/plain",
                            "type": "text",
                            "data": input_message.text,
                        }
                    )
                elif isinstance(input_message, UrlImageMessage):
                    image_url = input_message.image_url
                    content = None
                    mime_type = None
                    if image_url.startswith("data:"):
                        content, mime_type = image_url.split(",", 1)
                    elif image_url.startswith("http"):
                        content, mime_type = self.get_image_bytes_mime_type(image_url)
                    elif image_url.startswith("objref://"):
                        data_uri = self._get_session_asset_data_uri(image_url, include_name=True)
                        mime_type, _, content = validate_parse_data_uri(data_uri)
                    if content and mime_type:
                        parts.append(
                            {
                                "type": "blob",
                                "data": content,
                                "mime_type": mime_type,
                            }
                        )

            messages.append(
                {
                    "role": "user",
                    "content": parts,
                }
            )
        client = get_llm_client_from_provider_config(
            self.provider_slug(), self._config.model.model_name(), self.get_provider_config
        )
        provider_config = self.get_provider_config(
            provider_slug=self.provider_slug(), model_slug=self._config.model.model_name()
        )

        messages_to_send = (
            [{"role": "system", "content": self._config.system_message}] + messages
            if self._config.system_prompt
            else messages
        )

        response = client.chat.completions.create(
            messages=messages_to_send,
            model=self._config.model.model_name(),
            max_tokens=self._config.max_tokens,
            stream=True,
            temperature=self._config.temperature,
        )

        for result in response:
            if result.usage:
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                        MetricType.INPUT_TOKENS,
                        (provider_config.provider_config_source, result.usage.input_tokens),
                    )
                )
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                        MetricType.OUTPUT_TOKENS,
                        (provider_config.provider_config_source, result.usage.output_tokens),
                    )
                )

            choice = result.choices[0]
            if choice.delta.content:
                text_content = "".join(
                    list(map(lambda entry: entry["data"] if entry["type"] == "text" else "", choice.delta.content))
                )
                async_to_sync(self._output_stream.write)(MessagesOutput(message=text_content))
                text_content = ""

        output = self._output_stream.finalize()

        if self._config.retain_history:
            self._chat_history = copy.deepcopy(messages)
            self._chat_history.append(
                {
                    "role": "assistant",
                    "message": output.message,
                }
            )

        return output
