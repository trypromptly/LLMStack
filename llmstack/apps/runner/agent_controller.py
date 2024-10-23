import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict

from llmstack.common.blocks.base.schema import StrEnum
from llmstack.common.utils.liquid import render_template
from llmstack.common.utils.provider_config import get_matched_provider_config
from llmstack.common.utils.sslr.types.chat.chat_completion import ChatCompletion
from llmstack.common.utils.sslr.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class AgentControllerConfig(BaseModel):
    provider_configs: Dict[str, Any]
    provider_slug: str
    model_slug: str
    system_message: str
    tools: List[Dict]
    stream: bool = False
    realtime: bool = False
    max_steps: int = 30

    model_config = ConfigDict(protected_namespaces=())


class AgentControllerDataType(StrEnum):
    INPUT = "input"
    TOOL_CALLS = "tool_calls"
    TOOL_CALLS_END = "tool_calls_end"
    AGENT_OUTPUT = "agent_output"
    AGENT_OUTPUT_END = "agent_output_end"
    ERROR = "error"
    USAGE_DATA = "usage_data"


class AgentUsageData(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentMessageRole(StrEnum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"


class AgentMessageContentType(StrEnum):
    TEXT = "text"


class AgentMessageContent(BaseModel):
    type: AgentMessageContentType = AgentMessageContentType.TEXT
    data: Any = None


class AgentMessage(BaseModel):
    role: AgentMessageRole
    name: str = ""
    content: List[AgentMessageContent]


class AgentSystemMessage(AgentMessage):
    role: AgentMessageRole = AgentMessageRole.SYSTEM


class AgentAssistantMessage(AgentMessage):
    role: AgentMessageRole = AgentMessageRole.ASSISTANT


class AgentUserMessage(AgentMessage):
    role: AgentMessageRole = AgentMessageRole.USER


class AgentToolCall(BaseModel):
    id: str
    name: str
    arguments: str  # JSON string


class AgentToolCallsMessage(BaseModel):
    tool_calls: List[AgentToolCall] = []
    responses: Dict[str, Any] = {}  # Map of tool call id to output


class AgentControllerData(BaseModel):
    type: AgentControllerDataType
    data: Optional[Union[AgentUserMessage, AgentAssistantMessage, AgentToolCallsMessage, AgentUsageData]] = None


class AgentController:
    def __init__(self, output_queue: asyncio.Queue, config: AgentControllerConfig):
        self._output_queue = output_queue
        self._config = config
        self._messages: List[AgentMessage] = [
            AgentSystemMessage(
                role=AgentMessageRole.SYSTEM,
                content=[
                    AgentMessageContent(
                        type=AgentMessageContentType.TEXT,
                        data=render_template(self._config.system_message, {}),
                    )
                ],
            )
        ]

        self._init_llm_client()

    def _init_llm_client(self):
        """
        Initialize the LLM client
        """
        self._llm_client = get_llm_client_from_provider_config(
            self._config.provider_slug,
            self._config.model_slug,
            lambda provider_slug, model_slug: get_matched_provider_config(
                provider_configs=self._config.provider_configs,
                provider_slug=provider_slug,
                model_slug=model_slug,
            ),
        )

    def _convert_messages_to_llm_client_format(self):
        """
        Convert the messages to the format that the LLM client expects
        """
        client_messages = []
        for message in self._messages:
            if isinstance(message, AgentSystemMessage):
                client_messages.append({"role": "system", "content": message.content[0].data})
            elif isinstance(message, AgentAssistantMessage):
                client_messages.append({"role": "assistant", "content": message.content[0].data})
            elif isinstance(message, AgentUserMessage):
                content = message.content[0].data
                if isinstance(content, dict):
                    content = json.dumps(content)
                client_messages.append({"role": "user", "content": content})
            elif isinstance(message, AgentToolCallsMessage):
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        {
                            "type": "function",
                            "id": tool_call.id,
                            "function": {
                                "name": tool_call.name,
                                "arguments": tool_call.arguments,
                            },
                        }
                    )
                client_messages.append({"role": "assistant", "tool_calls": tool_calls})

                # Add the tool call responses to the client messages
                for tool_call_id, output in message.responses.items():
                    client_messages.append({"role": "tool", "content": output, "tool_call_id": tool_call_id})

        return client_messages

    def process(self, data: AgentControllerData):
        self._messages.append(data.data)

        try:
            if len(self._messages) > self._config.max_steps:
                raise Exception(f"Max steps ({self._config.max_steps}) exceeded: {len(self._messages)}")

            if data.type != AgentControllerDataType.AGENT_OUTPUT:
                self.process_messages()
        except Exception as e:
            logger.exception("Error processing messages")
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.ERROR,
                    data=AgentAssistantMessage(
                        content=[AgentMessageContent(data=str(e))],
                    ),
                )
            )

    def process_messages(self):
        """
        Call the LLM with the messages and the tools available
        """
        client_messages = self._convert_messages_to_llm_client_format()

        response = self._llm_client.chat.completions.create(
            model=self._config.model_slug,
            messages=client_messages,
            stream=self._config.stream,
            tools=self._config.tools,
        )

        if self._config.stream:
            for chunk in response:
                self.add_response_to_output_queue(chunk)
        else:
            self.add_response_to_output_queue(response)

    def add_response_to_output_queue(self, response: Any):
        """
        Add the response to the output queue as well as update _messages
        """
        if response.usage:
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.USAGE_DATA,
                    data=AgentUsageData(
                        prompt_tokens=response.usage.input_tokens,
                        completion_tokens=response.usage.output_tokens,
                        total_tokens=response.usage.total_tokens,
                    ),
                )
            )

        # For streaming responses, add the content to the output queue and messages
        if isinstance(response, ChatCompletionChunk) and response.choices[0].delta.content:
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.AGENT_OUTPUT,
                    data=AgentAssistantMessage(
                        content=[AgentMessageContent(data=response.choices[0].delta.content)],
                    ),
                )
            )

        # For non-streaming responses, add the tool calls to the output queue and messages
        if isinstance(response, ChatCompletion) and response.choices[0].message.tool_calls:
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.TOOL_CALLS,
                    data=AgentToolCallsMessage(
                        tool_calls=[
                            AgentToolCall(
                                id=tool_call.id,
                                name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                            )
                            for tool_call in response.choices[0].message.tool_calls
                        ]
                    ),
                )
            )

        # For streaming responses, add the tool calls chunks to the output queue
        if isinstance(response, ChatCompletionChunk) and response.choices[0].delta.tool_calls:
            tool_calls = []
            if len(response.choices[0].delta.tool_calls) == 1 and response.choices[0].delta.tool_calls[0].index > 0:
                tool_call_index = response.choices[0].delta.tool_calls[0].index
                tool_calls = [
                    AgentToolCall(
                        id="",
                        name="",
                        arguments="",
                    )
                    for _ in range(0, tool_call_index)
                ] + [
                    AgentToolCall(
                        id=tool_call.id or "",
                        name=tool_call.function.name or "",
                        arguments=tool_call.function.arguments or "",
                    )
                    for tool_call in response.choices[0].delta.tool_calls
                ]
            else:
                tool_calls = [
                    AgentToolCall(
                        id=tool_call.id or "",
                        name=tool_call.function.name or "",
                        arguments=tool_call.function.arguments or "",
                    )
                    for tool_call in response.choices[0].delta.tool_calls
                ]
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.TOOL_CALLS,
                    data=AgentToolCallsMessage(
                        tool_calls=tool_calls,
                    ),
                )
            )

        # For non-streaming responses, add the content to the output queue and messages
        if isinstance(response, ChatCompletion) and response.choices[0].message.content:
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.AGENT_OUTPUT,
                    data=AgentAssistantMessage(
                        content=[AgentMessageContent(data=choice.message.content) for choice in response.choices],
                    ),
                )
            )

        # Handle the end of the response
        if isinstance(response, ChatCompletion) or isinstance(response, ChatCompletionChunk):
            if response.choices[0].finish_reason == "stop":
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.AGENT_OUTPUT_END,
                    )
                )

            if response.choices[0].finish_reason == "tool_calls":
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.TOOL_CALLS_END,
                    )
                )
