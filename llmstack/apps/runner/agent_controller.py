import asyncio
import base64
import json
import logging
import queue
import ssl
import threading
from typing import Any, Dict, List, Optional, Union

import numpy as np
import websockets
from asgiref.sync import sync_to_async
from pydantic import BaseModel, ConfigDict
from pyrnnoise import RNNoise

from llmstack.apps.types.agent import AgentConfigSchema
from llmstack.apps.types.voice_agent import VoiceAgentConfigSchema
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
    agent_config: Union[AgentConfigSchema, VoiceAgentConfigSchema]
    is_voice_agent: bool = False
    tools: List[Dict]
    metadata: Dict[str, Any]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        # Convert agent_config to correct type if needed
        if "agent_config" in data:
            config = data["agent_config"]
            if isinstance(config, dict):
                if data.get("is_voice_agent", False):
                    data["agent_config"] = VoiceAgentConfigSchema(**config)
                else:
                    data["agent_config"] = AgentConfigSchema(**config)

        super().__init__(**data)

        if self.is_voice_agent and not isinstance(self.agent_config, VoiceAgentConfigSchema):
            raise ValueError("agent_config must be VoiceAgentConfigSchema when is_voice_agent is True")
        elif not self.is_voice_agent and not isinstance(self.agent_config, AgentConfigSchema):
            raise ValueError("agent_config must be AgentConfigSchema when is_voice_agent is False")


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
    provider: str = ""
    source: str = ""


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


def save_messages_to_session_data(session_id, id, messages: List[AgentMessage]):
    from llmstack.apps.app_session_utils import save_app_session_data

    logger.info(f"Saving messages to session data: {messages}")

    save_app_session_data(session_id, id, [m.model_dump_json() for m in messages])


def load_messages_from_session_data(session_id, id):
    from llmstack.apps.app_session_utils import get_app_session_data

    messages = []

    session_data = get_app_session_data(session_id, id)
    if session_data and isinstance(session_data, list):
        for data in session_data:
            data_json = json.loads(data)
            if data_json["role"] == "system":
                messages.append(AgentSystemMessage(**data_json))
            elif data_json["role"] == "assistant":
                messages.append(AgentAssistantMessage(**data_json))
            elif data_json["role"] == "user":
                messages.append(AgentUserMessage(**data_json))

    return messages


class AgentController:
    def __init__(self, output_queue: asyncio.Queue, config: AgentControllerConfig):
        self._session_id = config.metadata.get("session_id")
        self._controller_id = f"{config.metadata.get('app_uuid')}_agent"
        self._system_message = render_template(config.agent_config.system_message, {})
        self._output_queue = output_queue
        self._config = config
        self._messages: List[AgentMessage] = (
            load_messages_from_session_data(self._session_id, self._controller_id) or []
        )
        self._llm_client = None
        self._websocket = None
        self._provider_config = None

        self._input_text_stream = None
        self._input_audio_stream = None
        self._input_transcript_stream = None
        self._input_metadata = {}
        self._output_audio_stream = None
        self._output_transcript_stream = None
        self._rnnoise = RNNoise(sample_rate=24000)

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
                session["instructions"] = self._config.agent_config.system_message
                session["tools"] = [
                    {"type": "function", **t["function"]} for t in self._config.tools if t["type"] == "function"
                ]
                session["voice"] = self._config.agent_config.backend.voice

                if self._config.agent_config.input_audio_format:
                    session["input_audio_format"] = self._config.agent_config.input_audio_format
                if self._config.agent_config.output_audio_format:
                    session["output_audio_format"] = self._config.agent_config.output_audio_format

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

        self._provider_config = get_matched_provider_config(
            provider_configs=self._config.provider_configs,
            provider_slug=self._config.agent_config.backend.provider,
            model_slug=self._config.agent_config.backend.model,
        )

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

        model_slug = (
            "gpt-4o-realtime-preview"
            if self._config.agent_config.backend.model == "gpt-4o-realtime"
            else self._config.agent_config.backend.model
        )
        websocket_url = f"wss://api.openai.com/v1/realtime?model={model_slug}"
        headers = {
            "Authorization": f"Bearer {self._provider_config.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        self._websocket = await websockets.connect(
            websocket_url,
            extra_headers=headers,
            ssl=ssl_context,
        )
        logger.info(f"WebSocket connection for realtime mode initialized: {self._websocket}")

        # Handle websocket messages and input streams
        self._loop.create_task(self._handle_websocket_messages(), name="handle_websocket_messages")

        # Create an initial response
        await self._send_websocket_message({"type": "response.create"})

    def _init_llm_client(self):
        self._provider_config = get_matched_provider_config(
            provider_configs=self._config.provider_configs,
            provider_slug=self._config.agent_config.provider,
            model_slug=self._config.agent_config.model,
        )

        self._llm_client = get_llm_client_from_provider_config(
            self._config.agent_config.provider,
            self._config.agent_config.model,
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

                # Convert bytes to numpy array and normalize to float32
                try:
                    audio_data = np.frombuffer(chunk, dtype=np.int16)
                    # Convert int16 to float32 and normalize to [-1, 1]
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    frame_iterator = self._rnnoise.process_chunk(audio_data)
                except Exception as e:
                    logger.exception(f"Error processing chunk with rnnoise: {e}")
                    frame_iterator = []

                # Rebuild the chunk from the denoised frames
                denoised_chunk = b""
                try:
                    for _, denoised_frame in frame_iterator:
                        # Convert float32 [-1, 1] back to int16 range and then to bytes
                        int16_data = (denoised_frame * 32768.0).astype(np.int16)
                        denoised_chunk += int16_data.tobytes()
                except Exception as e:
                    logger.exception(f"Error joining denoised frames: {e}")

                logger.debug(f"Denoised chunk size to original chunk size: {len(denoised_chunk)} vs {len(chunk)}")

                # Base64 encode and send
                if len(denoised_chunk) > 0:
                    await self._send_websocket_message(
                        {"type": "input_audio_buffer.append", "audio": base64.b64encode(denoised_chunk).decode("utf-8")}
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

        # This is a message from the assistant to the user, simply add it to the message to maintain state
        if data.type == AgentControllerDataType.AGENT_OUTPUT_END or data.type == AgentControllerDataType.TOOL_CALLS_END:
            return

        try:
            if len(self._messages) > self._config.agent_config.max_steps:
                raise Exception(f"Max steps ({self._config.agent_config.max_steps}) exceeded: {len(self._messages)}")

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
        if self._config.is_voice_agent and self._config.agent_config.backend.backend_type == "multi_modal":
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
            stream = True if self._config.agent_config.stream is None else self._config.agent_config.stream
            response = self._llm_client.chat.completions.create(
                model=self._config.agent_config.model,
                messages=[{"role": "system", "content": self._system_message}] + client_messages,
                stream=stream,
                tools=self._config.tools,
            )

            if stream:
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
                        prompt_tokens=response.usage.get_input_tokens(),
                        completion_tokens=response.usage.get_output_tokens(),
                        total_tokens=response.usage.total_tokens,
                        source=self._provider_config.provider_config_source,
                        provider=str(self._provider_config),
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
        elif event_type == "input_audio_buffer.speech_stopped":
            pass
        elif event_type == "conversation.item.input_audio_transcription.completed":
            pass
        elif event_type == "error":
            logger.error(f"WebSocket error: {event}")

    def terminate(self):
        # Save to session data
        save_messages_to_session_data(self._session_id, self._controller_id, self._messages)

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
