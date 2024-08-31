import copy
import logging
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class MessagesModel(str, Enum):
    CLAUDE_3_Opus = "claude-3-opus"
    CLAUDE_3_Sonnet = "claude-3-sonnet"
    CLAUDE_3_Haiku = "claude-3-haiku"
    CLAUDE_3_5_Sonnet = "claude-3-5-sonnet"

    def __str__(self):
        return self.value

    def model_name(self):
        if self.value == "claude-3-opus":
            return "claude-3-opus-20240229"
        elif self.value == "claude-3-sonnet":
            return "claude-3-sonnet-20240229"
        elif self.value == "claude-3-haiku":
            return "claude-3-haiku-20240307"
        elif self.value == "claude-3-5-sonnet":
            return "claude-3-5-sonnet-20240620"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

    def __str__(self):
        return self.value


class ChatMessage(ApiProcessorSchema):
    role: Role = Field(
        default=Role.USER,
        description="The role of the message. Can be 'system', 'user', 'assistant', or 'function'.",
    )
    message: str = Field(
        default="",
        description="The message text.",
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
    message: str = Field(description="The response message.")


class MessagesConfiguration(ApiProcessorSchema):
    system_prompt: str = Field(
        default="",
        description="A system prompt is a way of providing context and instructions to Claude, such as specifying a particular goal or role.",
        json_schema_extra={"widget": "textarea", "advanced_parameter": False},
    )

    model: MessagesModel = Field(
        default=MessagesModel.CLAUDE_3_Opus,
        description="The model that will generate the responses.",
        json_schema_extra={"advanced_parameter": False},
    )
    max_tokens: int = Field(
        ge=1,
        default=256,
        description="The maximum number of tokens to generate before stopping.",
        json_schema_extra={"advanced_parameter": False},
    )
    temperature: float = Field(
        default=0.5,
        description="Amount of randomness injected into the response.",
        multiple_of=0.1,
        ge=0.0,
        le=1.0,
        json_schema_extra={"advanced_parameter": False},
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
    )


class MessagesProcessor(ApiProcessorInterface[MessagesInput, MessagesOutput, MessagesConfiguration]):
    @staticmethod
    def name() -> str:
        return "Messages"

    @staticmethod
    def slug() -> str:
        return "messages"

    @staticmethod
    def description() -> str:
        return "Claude chat messages"

    @staticmethod
    def provider_slug() -> str:
        return "anthropic"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{{message}}""",
        )

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history:
            return {"chat_history": self._chat_history}

        return {}

    def process(self) -> MessagesOutput:
        client = get_llm_client_from_provider_config(
            "anthropic", self._config.model.model_name(), self.get_provider_config
        )
        self._billing_metrics = self.get_provider_config(
            model_slug=self._config.model.value, provider_slug=self.provider_slug(), processor_slug=self.slug()
        ).get_billing_metrics(
            model_slug=self._config.model.value, provider_slug=self.provider_slug(), processor_slug=self.slug()
        )

        messages = self._chat_history if self._config.retain_history else []

        for message in self._input.messages:
            messages.append({"role": str(message.role), "content": str(message.message)})

        messages_to_send = (
            [{"role": "system", "content": self._config.system_prompt}] + messages
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
                self._usage_data["input_tokens"] = result.usage.input_tokens
                self._usage_data["output_tokens"] = result.usage.output_tokens

            choice = result.choices[0]
            if choice.delta.content:
                if isinstance(choice.delta.content, list):
                    text_content = "".join(
                        list(map(lambda entry: entry["data"] if entry["type"] == "text" else "", choice.delta.content))
                    )
                else:
                    text_content = choice.delta.content
                async_to_sync(self._output_stream.write)(MessagesOutput(message=text_content))
                text_content = ""

        output = self._output_stream.finalize()
        if self._config.retain_history:
            self._chat_history = copy.deepcopy(messages)
            self._chat_history.append({"role": "assistant", "message": output.message})

        return output
