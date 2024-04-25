import logging
from enum import Enum
from typing import Optional

import cohere
from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class CohereModel(str, Enum):
    COMMAND = "command"
    COMMAND_LIGHT = "command-light"
    COMMAND_LIGHT_NIGHTLY = "command-light-nightly"
    COMMAND_NIGHTLY = "command-nightly"
    COMMAND_R = "command-r"
    COMMAND_R_PLUS = "command-r-plus"

    def __str__(self):
        return self.value


class CoherePromptTruncation(str, Enum):
    OFF = "OFF"
    AUTO = "AUTO"
    AUTO_PRESERVE_ORDER = "AUTO_PRESERVE_ORDER"

    def __str__(self):
        return self.value


class CohereChatInput(ApiProcessorSchema):
    message: str = Field(
        description="The input message to send to cohere",
        widget="textarea",
        default="",
    )


class CohereChatConfiguration(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        description="The system message to send to cohere as preamble",
        widget="textarea",
        default=None,
        advanced_parameter=False,
    )
    temperature: float = Field(
        description="The temperature to use for sampling",
        default=0.7,
        multiple_of=0.1,
        ge=0.0,
        le=1.0,
        advanced_parameter=False,
    )
    model: CohereModel = Field(
        description="The model to use for the chat",
        default=CohereModel.COMMAND,
        advanced_parameter=False,
    )
    seed: Optional[int] = Field(
        description="The seed to use for sampling",
        default=None,
    )
    prompt_truncation: Optional[CoherePromptTruncation] = Field(
        description="Whether to truncate the prompt",
        default=CoherePromptTruncation.AUTO,
    )
    max_tokens: Optional[int] = Field(
        description="The maximum number of tokens to generate",
        default=256,
        gt=0,
        lt=8096,
    )
    retain_history: Optional[bool] = Field(
        description="Whether to retain the chat history",
        default=False,
    )
    enable_web_search: Optional[bool] = Field(
        description="Whether to enable web search",
        default=False,
        advanced_parameter=False,
    )


class CohereChatOutput(ApiProcessorSchema):
    output_message: str = Field(
        description="The output message from cohere",
        widget="textarea",
        default="",
    )


class CohereChatProcessor(
    ApiProcessorInterface[CohereChatInput, CohereChatOutput, CohereChatConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Cohere Chat"

    @staticmethod
    def slug() -> str:
        return "cohere_chat"

    @staticmethod
    def description() -> str:
        return "Cohere's Chat model, generates a text response to a user message."

    @staticmethod
    def provider_slug() -> str:
        return "cohere"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{{output_message}}""",
        )

    def process_session_data(self, session_data):
        self._chat_history = session_data.get("chat_history", [])

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history}

    def process(self) -> dict:
        history = self._chat_history if self._config.retain_history else []

        output_stream = self._output_stream
        client = cohere.Client(self._env["cohere_api_key"])
        response = client.chat_stream(
            preamble=self._config.system_message,
            chat_history=list(map(lambda x: cohere.types.ChatMessage(**x), history)),
            model=str(self._config.model),
            message=self._input.message,
            temperature=self._config.temperature,
            seed=self._config.seed,
            prompt_truncation=self._config.prompt_truncation,
            max_tokens=self._config.max_tokens,
            connectors=[] if not self._config.enable_web_search else [{"id": "web-search"}],
        )

        for event in response:
            if event.event_type == "text-generation":
                async_to_sync(output_stream.write)(CohereChatOutput(output_message=event.text))

        output = self._output_stream.finalize()
        if self._config.retain_history:
            history = history + [
                {"role": "USER", "message": self._input.message},
                {"role": "CHATBOT", "message": output.output_message},
            ]
            self._chat_history = history

        return output
