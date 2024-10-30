import asyncio
import base64
import json
import logging
import queue
import ssl
import threading
from typing import Any, Dict, List, Optional, Union

import websockets
from asgiref.sync import sync_to_async
from pydantic import BaseModel, ConfigDict

from llmstack.common.blocks.base.schema import StrEnum
from llmstack.common.utils.liquid import render_template
from llmstack.common.utils.provider_config import get_matched_provider_config
from llmstack.common.utils.sslr.types.chat.chat_completion import ChatCompletion
from llmstack.common.utils.sslr.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
)
from llmstack.processors.providers.config import ProviderConfig
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config

logger = logging.getLogger(__name__)


class AgentControllerConfig(BaseModel):
    provider_configs: Dict[str, Any]
    provider_config: ProviderConfig
    provider_slug: str
    model_slug: str
    system_message: str
    tools: List[Dict]
    stream: bool = False
    realtime: bool = False
    max_steps: int = 30
    metadata: Dict[str, Any]
    model_config = ConfigDict(protected_namespaces=())


class AgentControllerDataType(StrEnum):
    INPUT = "input"
    INPUT_STREAM = "input_stream"
    OUTPUT_STREAM = "output_stream"
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
    TEXT_STREAM = "text_stream"
    AUDIO_STREAM = "audio_stream"
    TRANSCRIPT_STREAM = "transcript_stream"
    METADATA = "metadata"


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
    data: Optional[
        Union[AgentSystemMessage, AgentUserMessage, AgentAssistantMessage, AgentToolCallsMessage, AgentUsageData]
    ] = None


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
        self._llm_client = None
        self._websocket = None

        self._input_text_stream = None
        self._input_audio_stream = None
        self._input_transcript_stream = None
        self._input_metadata = {}
        self._output_audio_stream = None
        self._output_transcript_stream = None

        self._input_messages_queue = queue.Queue()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._process_messages_loop())

    async def _handle_websocket_messages(self):
        while self._websocket.open:
            response = await self._websocket.recv()
            event = json.loads(response)

            if event["type"] == "session.created":
                logger.info(f"Session created: {event['session']['id']}")
                session = {}
                session["instructions"] = self._config.system_message
                session["tools"] = [
                    {"type": "function", **t["function"]} for t in self._config.tools if t["type"] == "function"
                ]

                updated_session = {
                    "type": "session.update",
                    "session": session,
                }
                await self._send_websocket_message(updated_session)
            elif event["type"] == "session.updated":
                pass
            else:
                await self.add_ws_event_to_output_queue(event)

    async def _init_websocket_connection(self):
        from llmstack.apps.models import AppSessionFiles
        from llmstack.assets.stream import AssetStream

        # Create the output streams
        self._output_audio_stream = AssetStream(
            await sync_to_async(AppSessionFiles.create_streaming_asset)(
                metadata={**self._config.metadata, "mime_type": "audio/wav"},
                ref_id=self._config.metadata.get("session_id"),
            )
        )
        self._output_transcript_stream = AssetStream(
            await sync_to_async(AppSessionFiles.create_streaming_asset)(
                metadata={**self._config.metadata, "mime_type": "text/plain"},
                ref_id=self._config.metadata.get("session_id"),
            )
        )

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        websocket_url = f"wss://api.openai.com/v1/realtime?model={self._config.model_slug}"
        headers = {
            "Authorization": f"Bearer {self._config.provider_config.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        self._websocket = await websockets.connect(
            websocket_url,
            extra_headers=headers,
            ssl=ssl_context,
        )
        logger.info(f"WebSocket connection for realtime mode initialized: {self._websocket}")

        # Handle websocket messages and input streams
        self._loop.create_task(self._handle_websocket_messages())

    def _init_llm_client(self):
        self._llm_client = get_llm_client_from_provider_config(
            self._config.provider_slug,
            self._config.model_slug,
            lambda provider_slug, model_slug: get_matched_provider_config(
                provider_configs=self._config.provider_configs,
                provider_slug=provider_slug,
                model_slug=model_slug,
            ),
        )

    async def _process_input_audio_stream(self):
        if self._input_audio_stream:
            async for chunk in self._input_audio_stream.read_async():
                if len(chunk) == 0:
                    await self._send_websocket_message({"type": "response.create"})
                    break

                # Base64 encode and send
                await self._send_websocket_message(
                    {"type": "input_audio_buffer.append", "audio": base64.b64encode(chunk).decode("utf-8")}
                )

    async def _process_input_text_stream(self):
        if self._input_text_stream:
            async for chunk in self._input_text_stream.read_async():
                await self._send_websocket_message(
                    {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": chunk.decode("utf-8")}],
                        },
                    }
                )

                # Cancel the previous response and create a new one
                await self._send_websocket_message({"type": "response.cancel"})
                await self._send_websocket_message({"type": "response.create"})

                # Let the client know that we just got a new message so it can interrupt the playing audio
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.INPUT_STREAM,
                    )
                )

    async def _process_messages_loop(self):
        while True:
            try:
                data = await self._loop.run_in_executor(None, self._input_messages_queue.get, True, 0.1)
                await self.process_messages(data)
            except queue.Empty:
                continue
            except asyncio.CancelledError:
                logger.info("Message processing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                await self._output_queue.put(
                    AgentControllerData(
                        type=AgentControllerDataType.ERROR,
                        data=AgentAssistantMessage(
                            content=[AgentMessageContent(data=str(e))],
                        ),
                    )
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
        # Actor calls this to add a message to the conversation and trigger processing
        self._messages.append(data.data)

        try:
            if len(self._messages) > self._config.max_steps:
                raise Exception(f"Max steps ({self._config.max_steps}) exceeded: {len(self._messages)}")

            if data.type != AgentControllerDataType.AGENT_OUTPUT:
                self._input_messages_queue.put(data)
        except Exception as e:
            logger.exception(f"Error processing messages: {e}")
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.ERROR,
                    data=AgentAssistantMessage(
                        content=[AgentMessageContent(data=str(e))],
                    ),
                )
            )

    async def process_messages(self, data: AgentControllerData):
        if self._config.realtime:
            if not self._websocket:
                await self._init_websocket_connection()

            # Use the data we just got from input queue when in realtime mode
            if data.type == AgentControllerDataType.INPUT_STREAM:
                # Use data from AssetStreams and respond accordingly
                for content in data.data.content:
                    if content.type == AgentMessageContentType.TEXT_STREAM:
                        self._input_text_stream = content.data
                    elif content.type == AgentMessageContentType.AUDIO_STREAM:
                        self._input_audio_stream = content.data
                    elif content.type == AgentMessageContentType.TRANSCRIPT_STREAM:
                        self._input_transcript_stream = content.data
                    elif content.type == AgentMessageContentType.METADATA:
                        self._input_metadata = content.data

                # Process the input streams
                self._input_audio_stream_task = self._loop.create_task(self._process_input_audio_stream())
                self._input_text_stream_task = self._loop.create_task(self._process_input_text_stream())

                # Send output_stream info to the client
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.OUTPUT_STREAM,
                        data=AgentSystemMessage(
                            content=[
                                AgentMessageContent(
                                    type=AgentMessageContentType.AUDIO_STREAM,
                                    data=self._output_audio_stream.objref,
                                ),
                                AgentMessageContent(
                                    type=AgentMessageContentType.TRANSCRIPT_STREAM,
                                    data=self._output_transcript_stream.objref,
                                ),
                            ]
                        ),
                    )
                )
            elif data.type == AgentControllerDataType.TOOL_CALLS:
                for tool_call_id, response in data.data.responses.items():
                    await self._send_websocket_message(
                        {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": tool_call_id,
                                "output": response,
                            },
                        }
                    )
                    await self._send_websocket_message({"type": "response.create"})
        else:
            if not self._llm_client:
                self._init_llm_client()

            client_messages = self._convert_messages_to_llm_client_format()
            response = self._llm_client.chat.completions.create(
                model=self._config.model_slug,
                messages=client_messages,
                stream=self._config.stream,
                tools=self._config.tools,
            )

            if self._config.stream:
                for chunk in response:
                    self.add_llm_client_response_to_output_queue(chunk)
            else:
                self.add_llm_client_response_to_output_queue(response)

    async def _send_websocket_message(self, message):
        await self._websocket.send(json.dumps(message))

    def add_llm_client_response_to_output_queue(self, response: Any):
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

    async def add_ws_event_to_output_queue(self, event: Any):
        event_type = event["type"]

        if event_type == "conversation.item.created":
            if event["item"]["type"] == "message":
                content_list = event["item"]["content"]
                for content_item in content_list:
                    if content_item["type"] == "text":
                        text = content_item["text"]
                        self._output_queue.put_nowait(
                            AgentControllerData(
                                type=AgentControllerDataType.AGENT_OUTPUT,
                                data=AgentAssistantMessage(
                                    content=[AgentMessageContent(data=text)],
                                ),
                            )
                        )
            elif event["item"]["type"] == "function_call":
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.TOOL_CALLS,
                        data=AgentToolCallsMessage(
                            tool_calls=[
                                AgentToolCall(
                                    id=event["item"]["call_id"],
                                    name=event["item"]["name"],
                                    arguments=event["item"]["arguments"],
                                )
                            ],
                        ),
                    )
                )
        elif event_type == "response.function_call_arguments.delta":
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.TOOL_CALLS,
                    data=AgentToolCallsMessage(
                        tool_calls=[
                            AgentToolCall(
                                id="",
                                name="",
                                arguments=event.get("delta", ""),
                            )
                        ],
                    ),
                )
            )
        elif event_type == "response.function_call_arguments.done":
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.TOOL_CALLS_END,
                )
            )
        elif event_type == "response.text.delta":
            delta = event["delta"]
            try:
                text = json.loads(delta)["text"]
            except Exception as e:
                logger.error(e)
                text = delta
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.AGENT_OUTPUT,
                    data=AgentAssistantMessage(
                        content=[AgentMessageContent(data=text)],
                    ),
                )
            )
        elif event_type == "response.content_part.added":
            part = event["part"]
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.AGENT_OUTPUT,
                    data=AgentAssistantMessage(
                        content=[AgentMessageContent(data=part["text"] if part["type"] == "text" else "")],
                    ),
                )
            )
        elif event_type == "response.audio_transcript.delta":
            self._output_transcript_stream.append_chunk(event["delta"].encode("utf-8"))
        elif event_type == "response.audio.delta":
            if self._output_audio_stream:
                pcm_data = base64.b64decode(event["delta"])
                self._output_audio_stream.append_chunk(pcm_data)
        elif event_type == "response.done":
            if "response" in event and "usage" in event["response"]:
                usage = event["response"]["usage"]
                self._output_queue.put_nowait(
                    AgentControllerData(
                        type=AgentControllerDataType.USAGE_DATA,
                        data=AgentUsageData(
                            prompt_tokens=usage["input_tokens"],
                            completion_tokens=usage["output_tokens"],
                            total_tokens=usage["total_tokens"],
                        ),
                    )
                )
        elif event_type == "input_audio_buffer.speech_started":
            # We need to let the client know that the speech has started
            self._output_queue.put_nowait(
                AgentControllerData(
                    type=AgentControllerDataType.INPUT_STREAM,
                )
            )
        elif event_type == "error":
            logger.error(f"WebSocket error: {event}")

    def terminate(self):
        # Create task for graceful websocket closure
        if hasattr(self, "_websocket") and self._websocket:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)

        # Finalize streams
        if self._output_audio_stream:
            self._output_audio_stream.finalize()
        if self._output_transcript_stream:
            self._output_transcript_stream.finalize()
        if self._input_audio_stream:
            self._input_audio_stream.finalize()
        if self._input_transcript_stream:
            self._input_transcript_stream.finalize()

        # Cancel running tasks
        if hasattr(self, "_input_audio_stream_task") and self._input_audio_stream_task:
            self._input_audio_stream_task.cancel()
        if hasattr(self, "_input_text_stream_task") and self._input_text_stream_task:
            self._input_text_stream_task.cancel()

        # Wait for thread to finish
        self._thread.join(timeout=5)
        logger.info("Agent controller terminated")
