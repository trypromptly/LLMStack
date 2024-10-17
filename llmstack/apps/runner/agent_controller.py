import asyncio
import json
import logging
from typing import Any, Dict, List, Literal

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

    model_config = ConfigDict(protected_namespaces=())


class AgentControllerDataType(StrEnum):
    BEGIN = "BEGIN"
    INPUT = "INPUT"
    TOOL_CALL = "TOOL_CALL"
    TOOL_CALL_RESPONSE = "TOOL_CALL_RESPONSE"
    OUTPUT = "OUTPUT"
    ERROR = "ERROR"
    END = "END"


class AgentControllerData(BaseModel):
    type: AgentControllerDataType
    data: Any = None


class AgentMessageContent(BaseModel):
    type: str = "text"
    data: Any = None


class AgentMessage(BaseModel):
    type: str = "message"
    role: Literal["system", "assistant", "user", "tool"]
    content: List[AgentMessageContent]


class AgentSystemMessage(AgentMessage):
    role: Literal["system"] = "system"


class AgentAssistantMessage(AgentMessage):
    role: Literal["assistant"] = "assistant"


class AgentUserMessage(AgentMessage):
    role: Literal["user"] = "user"


class AgentToolCallFunction(BaseModel):
    name: str
    arguments: str  # JSON string


class AgentToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: AgentToolCallFunction


class AgentToolCallMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    tool_calls: List[AgentToolCall]


class AgentToolCallResponseMessage(BaseModel):
    tool_call_id: str
    output: str


class AgentController:
    def __init__(self, output_queue: asyncio.Queue, config: AgentControllerConfig):
        self._output_queue = output_queue
        self._config = config
        self._messages: List[AgentMessage] = [
            AgentSystemMessage(
                role="system",
                content=[
                    AgentMessageContent(
                        type="text",
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
            elif isinstance(message, AgentToolCallMessage):
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        {
                            "type": "function",
                            "id": tool_call.id,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )
                client_messages.append({"role": "assistant", "tool_calls": tool_calls})
            elif isinstance(message, AgentToolCallResponseMessage):
                client_messages.append(
                    {
                        "role": "tool",
                        "content": message.output,
                        "tool_call_id": message.tool_call_id,
                    }
                )
        return client_messages

    def process(self, input: AgentControllerData):
        if input.type == AgentControllerDataType.INPUT:
            self._messages.append(AgentUserMessage(content=[AgentMessageContent(data=input.data)]))
        elif input.type == AgentControllerDataType.TOOL_CALL_RESPONSE:
            self._messages.append(
                AgentToolCallResponseMessage(
                    output=input.data.get("output"),
                    tool_call_id=input.data.get("tool_call_id"),
                )
            )

        try:
            self.process_messages()
        except Exception as e:
            logger.exception("Error processing messages")
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.ERROR,
                    data=str(e),
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
            prev_chunks = []
            for chunk in response:
                self.add_response_to_output_queue(chunk, prev_chunks)
                prev_chunks.append(chunk)
        else:
            self.add_response_to_output_queue(response)

    def add_response_to_output_queue(self, response: Any, prev_responses: List[Any] = []):
        """
        Add the response to the output queue as well as update _messages
        """
        # For streaming responses, add the content to the output queue and messages
        if isinstance(response, ChatCompletionChunk) and response.choices[0].delta.content:
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.OUTPUT,
                    data={"content": response.choices[0].delta.content},
                )
            )
            self._messages.append(
                AgentAssistantMessage(
                    content=[AgentMessageContent(data=response.choices[0].delta.content)],
                )
            )

        # For streaming responses, add the tool calls chunks to the output queue
        if isinstance(response, ChatCompletionChunk) and response.choices[0].delta.tool_calls:
            output_tool_calls = []
            for tool_call in response.choices[0].delta.tool_calls:
                output_tool_calls.append(
                    {
                        "id": tool_call.id or "",
                        "name": tool_call.function.name or "",
                        "arguments": tool_call.function.arguments or "",
                    }
                )
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.OUTPUT,
                    data={"tool_calls": output_tool_calls},
                )
            )

        # Once the tool calls are done in streaming mode, stitch the chunks together to get the full tool calls output
        if isinstance(response, ChatCompletionChunk) and response.choices[0].finish_reason == "tool_calls":
            tool_calls = []
            for chunk in prev_responses:
                if chunk.choices[0].delta.tool_calls:
                    total_tool_calls = len(chunk.choices[0].delta.tool_calls)
                    for i in range(total_tool_calls):
                        tool_call = chunk.choices[0].delta.tool_calls[i]
                        if len(tool_calls) == i:
                            tool_calls.append(
                                {
                                    "id": "",
                                    "name": "",
                                    "arguments": "",
                                }
                            )

                        tool_calls[i]["id"] += tool_call.id or ""
                        tool_calls[i]["name"] += tool_call.function.name or ""
                        tool_calls[i]["arguments"] += tool_call.function.arguments or ""

            tool_call_objects = []
            for tool_call in tool_calls:
                tool_call_object = AgentToolCall(
                    id=tool_call["id"],
                    function=AgentToolCallFunction(
                        name=tool_call["name"],
                        arguments=tool_call["arguments"],
                    ),
                )
                tool_call_objects.append(tool_call_object)

                # Send tool call to agent actor
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.TOOL_CALL,
                        data=tool_call_object,
                    )
                )

            # Add tool calls to messages
            self._messages.append(
                AgentToolCallMessage(
                    tool_calls=tool_call_objects,
                )
            )

        # For non-streaming responses, add the tool calls to the output queue and messages
        if isinstance(response, ChatCompletion) and response.choices[0].message.tool_calls:
            tool_calls = []
            for tool_call in response.choices[0].message.tool_calls:
                tool_calls.append(
                    AgentToolCall(
                        id=tool_call.id,
                        function=AgentToolCallFunction(
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        ),
                    )
                )
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.TOOL_CALL,
                        data=tool_call,
                    )
                )
            self._messages.append(
                AgentToolCallMessage(
                    tool_calls=tool_calls,
                )
            )

        # For non-streaming responses, add the content to the output queue and messages
        if isinstance(response, ChatCompletion) and response.choices[0].message.content:
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.OUTPUT,
                    data={"content": response.choices[0].message.content},
                )
            )
            self._messages.append(
                AgentAssistantMessage(
                    content=[AgentMessageContent(data=response.choices[0].message.content)],
                )
            )

        # Handle the end of the response
        if (isinstance(response, ChatCompletion) or isinstance(response, ChatCompletionChunk)) and response.choices[
            0
        ].finish_reason == "stop":
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.END,
                )
            )
