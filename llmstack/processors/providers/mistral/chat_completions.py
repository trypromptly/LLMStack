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

logger = logging.getLogger(__name__)


class MessagesModel(str, Enum):
    MISTRAL_7B = "open-mistral-7b"
    MIXTRAL_7B = "open-mixtral-8x7b"
    MIXTRAL_22B = "open-mixtral-8x22b"
    MIXTRAL_SMALL = "mistral-small-latest"
    MIXTRAL_MEDIUM = "mistral-medium-latest"
    MIXTRAL_LARGE = "mistral-large-latest"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"

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
    result: str = Field(description="The response message.")


class MessagesConfiguration(ApiProcessorSchema):
    system_prompt: str = Field(
        default="",
        description="A system prompt is a way of providing context and instructions to the model.",
        json_schema_extra={"widget": "textarea", "advanced_parameter": False},
    )

    model: MessagesModel = Field(
        default=MessagesModel.MIXTRAL_SMALL,
        description="The Mistral model that will generate the responses.",
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
    safe_prompt: Optional[bool] = Field(
        default=False,
        description="Whether to inject a safety prompt before all conversations.",
    )
    seed: Optional[int] = Field(
        default=None,
        description="The seed to use for random sampling. If set, different calls will generate deterministic results.",
    )


class MessagesProcessor(ApiProcessorInterface[MessagesInput, MessagesOutput, MessagesConfiguration]):
    @staticmethod
    def name() -> str:
        return "Chat Completions"

    @staticmethod
    def slug() -> str:
        return "chat_completions"

    @staticmethod
    def description() -> str:
        return "Mistral Chat Completions"

    @staticmethod
    def provider_slug() -> str:
        return "mistral"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{{ result }}""",
        )

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history:
            return {"chat_history": self._chat_history}
        return {}

    def process(self) -> MessagesOutput:
        from llmstack.common.utils.sslr import LLM

        client = LLM(
            provider="mistral",
            mistral_api_key=self._env.get("mistral_api_key"),
        )
        messages = []

        if self._config.system_prompt:
            messages.append({"role": "system", "content": self._config.system_message})

        if self._chat_history:
            for message in self._chat_history:
                messages.append({"role": message["role"], "content": message["message"]})

        for message in self._input.messages:
            messages.append({"role": str(message.role), "content": str(message.message)})

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
                async_to_sync(self._output_stream.write)(MessagesOutput(result=choice.delta.content))

        output = self._output_stream.finalize()

        if self._config.retain_history:
            for message in self._input.messages:
                self._chat_history.append({"role": str(message.role), "message": str(message.message)})

            self._chat_history.append({"role": "assistant", "message": output.message})

        return output
