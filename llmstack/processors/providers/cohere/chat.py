import copy
import logging
from enum import Enum
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

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

    def model_name(self):
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
        json_schema_extra={"widget": "textarea"},
        default="",
    )


class CohereChatConfiguration(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        description="The system message to send to cohere as preamble",
        default=None,
        json_schema_extra={"advanced_parameter": False, "widget": "textarea"},
    )
    temperature: float = Field(
        description="The temperature to use for sampling",
        default=0.7,
        multiple_of=0.1,
        ge=0.0,
        le=1.0,
        json_schema_extra={"advanced_parameter": False},
    )
    model: CohereModel = Field(
        description="The model to use for the chat",
        default=CohereModel.COMMAND,
        json_schema_extra={"advanced_parameter": False},
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
        json_schema_extra={"advanced_parameter": False},
    )


class CohereChatOutput(ApiProcessorSchema):
    output_message: str = Field(
        description="The output message from cohere",
        json_schema_extra={"widget": "textarea"},
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
        client = get_llm_client_from_provider_config("cohere", self._config.model.value, self.get_provider_config)

        messages = self._chat_history if self._config.retain_history else []

        if self._input.message:
            messages.append({"role": "user", "content": self._input.message})

        messages_to_send = (
            [{"role": "system", "content": self._config.system_message}] + messages
            if self._config.system_message
            else messages
        )

        response = client.chat.completions.create(
            messages=messages_to_send,
            model=self._config.model.value,
            seed=self._config.seed,
            prompt_truncation=self._config.prompt_truncation,
            max_tokens=self._config.max_tokens,
            stream=True,
            temperature=self._config.temperature,
            connectors=[{"id": "web-search"}] if self._config.enable_web_search else [],
        )

        for result in response:
            if result.usage:
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                        MetricType.INPUT_TOKENS,
                        result.usage.input_tokens,
                    )
                )
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/*/{self._config.model.model_name()}/*",
                        MetricType.OUTPUT_TOKENS,
                        result.usage.output_tokens,
                    )
                )

            choice = result.choices[0]
            if choice.delta.content:
                if isinstance(choice.delta.content, list):
                    text_content = "".join(
                        list(map(lambda entry: entry["data"] if entry["type"] == "text" else "", choice.delta.content))
                    )
                else:
                    text_content = choice.delta.content
                async_to_sync(self._output_stream.write)(CohereChatOutput(output_message=text_content))
                text_content = ""

        output = self._output_stream.finalize()
        if self._config.retain_history:
            self._chat_history = copy.deepcopy(messages)
            self._chat_history.append({"role": "assistant", "content": output.output_message})

        return output
