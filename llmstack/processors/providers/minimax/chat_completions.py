import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field, model_validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class MessagesModel(StrEnum):
    MINIMAX_M3 = "MiniMax-M3"
    MINIMAX_M2_7 = "MiniMax-M2.7"

    def model_name(self):
        return self.value


class ThinkingType(StrEnum):
    ADAPTIVE = "adaptive"
    DISABLED = "disabled"


class Role(StrEnum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class ChatMessage(ApiProcessorSchema):
    role: Role = Field(
        default=Role.USER,
        description="The role of the message. Can be 'system', 'user', or 'assistant'.",
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
        default=MessagesModel.MINIMAX_M3,
        description="The MiniMax model that will generate the responses.",
        json_schema_extra={"advanced_parameter": False},
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
        description=("Thinking mode for MiniMax-M3. MiniMax-M2.7 always keeps thinking enabled."),
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
    )

    @model_validator(mode="after")
    def validate_thinking(self):
        if self.model == MessagesModel.MINIMAX_M2_7 and self.thinking == ThinkingType.DISABLED:
            raise ValueError("MiniMax-M2.7 does not support disabling thinking")
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
        from llmstack.common.utils.sslr import LLM

        minimax_provider_config = self.get_provider_config(model_slug=self._config.model.model_name())
        client = LLM(
            provider="openai",
            openai_api_key=minimax_provider_config.api_key,
            openai_base_url=minimax_provider_config.base_url,
        )
        messages = []

        if self._config.system_prompt:
            messages.append({"role": "system", "content": self._config.system_prompt})

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
            extra_body={"thinking": {"type": self._config.thinking.value}},
        )

        for result in response:
            choice = result.choices[0]
            if choice.delta.content:
                async_to_sync(self._output_stream.write)(MessagesOutput(result=choice.delta.content))

        output = self._output_stream.finalize()

        if self._config.retain_history:
            for message in self._input.messages:
                self._chat_history.append({"role": str(message.role), "message": str(message.message)})

            self._chat_history.append({"role": "assistant", "message": output.result})

        return output
