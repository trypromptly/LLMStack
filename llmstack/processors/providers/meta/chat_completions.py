import json
import logging
import os
from enum import Enum
from typing import Iterator, List, Optional

import requests
from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.connections.models import ConnectionType
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.google import get_google_credential_from_env

logger = logging.getLogger(__name__)


class Llama3ChatFormat:
    def __init__(self):
        pass

    def add_header(self, message):
        tokens = []
        tokens.append("<|start_header_id|>")
        tokens.extend([message["role"]])
        tokens.append("<|end_header_id|>")
        tokens.extend("\n\n")
        return tokens

    def add_message(self, message):
        tokens = self.add_header(message)
        tokens.extend([message["content"].strip()])
        tokens.append("<|eot_id|>")
        return tokens

    def prompt(self, dialog, system) -> str:
        tokens = []
        tokens.append("<|begin_of_text|>")
        if system:
            tokens.extend(self.add_message({"role": "system", "content": system}))
        for message in dialog:
            tokens.extend(self.add_message(message))
        # Add the start of an assistant message for the model to complete.
        tokens.extend(self.add_header({"role": "assistant", "content": ""}))
        return "".join(tokens)


def _iter_bytes(response_bytes: bytes) -> Iterator[bytes]:
    start = 0
    while start < len(response_bytes):
        end = response_bytes.find(b"\x00", start)
        if end == -1:
            end = len(response_bytes)
        yield response_bytes[start:end]
        start = end + 1


class MessagesModel(str, Enum):
    LLAMA_3_8B = "llama-3-8b"

    def __str__(self):
        return self.value

    def model_name(self):
        return self.value


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"

    def __str__(self):
        return self.value


class ChatMessage(ApiProcessorSchema):
    role: Role = Field(
        default=Role.USER,
        description="The role of the message. Can be 'system', 'user' or 'assistant'.",
    )
    message: str = Field(
        default="",
        description="The message text.",
        widget="textarea",
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
        default="You are a helpful assistant.",
        description="A system prompt is a way of providing context and instructions to the model.",
        widget="textarea",
        advanced_parameter=False,
    )
    model: MessagesModel = Field(
        default=MessagesModel.LLAMA_3_8B,
        description="The Llama model that will generate the responses.",
        advanced_parameter=False,
    )
    max_tokens: int = Field(
        ge=1,
        default=256,
        description="The maximum number of tokens to generate before stopping.",
        advanced_parameter=False,
    )
    temperature: float = Field(
        default=0.5,
        description="Amount of randomness injected into the response.",
        multiple_of=0.1,
        ge=0.0,
        le=1.0,
        advanced_parameter=False,
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
    )
    top_k: Optional[bool] = Field(
        default=False,
        description="Whether to inject a safety prompt before all conversations.",
    )
    seed: Optional[int] = Field(
        default=None,
        description="The seed to use for random sampling. If set, different calls will generate deterministic results.",
    )
    vertex_url: Optional[str] = Field(
        default=None,
        description="The URL to the Vertex AI endpoint.",
    )
    connection_id: Optional[str] = Field(
        widget="connection",
        advanced_parameter=False,
        description="Select a connection to use for the Vertex AI endpoint.",
        filters=[ConnectionType.CREDENTIALS + "/bearer_authentication"],
    )
    top_p: Optional[float] = Field(
        default=0.9,
        description="The cumulative probability of the top tokens to sample from.",
        multiple_of=0.1,
        ge=0.0,
        le=1.0,
        advanced_parameter=False,
    )
    repetition_penalty: Optional[float] = Field(
        default=1.0,
        description="The penalty for repeating the same token.",
        multiple_of=0.1,
        advanced_parameter=False,
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
        return "Llama Chat Completions"

    @staticmethod
    def provider_slug() -> str:
        return "meta"

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history:
            return {"chat_history": self._chat_history}
        return {}

    def process(self) -> MessagesOutput:
        messages = []

        connection = (
            self._env["connections"].get(
                self._config.connection_id,
                None,
            )
            if self._config.connection_id
            else None
        )

        url = self._config.vertex_url
        if connection and connection["base_connection_type"] == ConnectionType.CREDENTIALS:
            token = connection["configuration"]["token"]
            token_prefix = connection["configuration"]["token_prefix"]

        if connection is None and self._config.vertex_url is None:
            google_api_key, token_type = (
                get_google_credential_from_env(self._env) if self._env.get("google_service_account_json_key") else None
            )
            token_prefix = "Bearer"
            token = google_api_key
            url = os.getenv("VERTEX_LLAM3_8B_URL")

        if self._chat_history:
            for message in self._chat_history:
                messages.append({"role": message["role"], "content": message["message"]})

        for message in self._input.messages:
            messages.append({"role": str(message.role), "content": str(message.message)})

        prompt = Llama3ChatFormat().prompt(messages, system=self._config.system_prompt)
        response = requests.post(
            url=url,
            headers={"Authorization": f"{token_prefix} {token}"},
            json={
                "instances": [
                    {
                        "prompt": prompt,
                        "temperature": self._config.temperature,
                        "top_p": self._config.top_p,
                        "repetition_penalty": self._config.repetition_penalty,
                        "max_tokens": self._config.max_tokens,
                        "stream": True,
                        "stop": ["<|eot_id|>"],
                    }
                ],
                "parameters": {},
            },
            stream=True,
        )
        if response.status_code == 200:
            for response_bytes in _iter_bytes(response.content):
                json_chunk = json.loads(response_bytes.decode("utf-8"))
                async_to_sync(self._output_stream.write)(MessagesOutput(result=json_chunk["predictions"][0]))
        else:
            response.raise_for_status()

        output = self._output_stream.finalize()

        if self._config.retain_history:
            for message in self._input.messages:
                self._chat_history.append({"role": str(message.role), "message": str(message.message)})

            self._chat_history.append({"role": "assistant", "message": output.message})

        return output
