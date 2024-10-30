import asyncio
import json
import logging
import time
from typing import Any, Dict, List

from llmstack.apps.runner.agent_controller import (
    AgentController,
    AgentControllerConfig,
    AgentControllerData,
    AgentControllerDataType,
    AgentMessageContent,
    AgentMessageContentType,
    AgentToolCallsMessage,
    AgentUserMessage,
)
from llmstack.apps.runner.output_actor import OutputActor
from llmstack.common.utils.liquid import render_template
from llmstack.common.utils.provider_config import get_matched_provider_config
from llmstack.play.actor import BookKeepingData
from llmstack.play.messages import ContentData, Error, Message, MessageType
from llmstack.play.output_stream import stitch_model_objects
from llmstack.play.utils import run_coro_in_new_loop
from llmstack.processors.providers.config import ProviderConfigSource
from llmstack.processors.providers.metrics import MetricType

logger = logging.getLogger(__name__)


class AgentActor(OutputActor):
    def __init__(
        self,
        coordinator_urn: str,
        dependencies: list = [],
        templates: Dict[str, str] = {},
        agent_config: Dict[str, Any] = {},
        metadata: Dict[str, Any] = {},
        provider_configs: Dict[str, Any] = {},
        tools: List[Dict] = [],
        bookkeeping_queue: asyncio.Queue = None,
    ):
        self._process_output_task = None
        self._config = agent_config
        self._provider_configs = provider_configs
        self._provider_slug = self._config.get("provider_slug", "openai")
        self._model_slug = self._config.get("model", "gpt-4o-mini")
        self._provider_config = get_matched_provider_config(
            provider_configs=self._provider_configs,
            provider_slug=self._provider_slug,
            model_slug=self._model_slug,
        )
        self._realtime = self._config.get("realtime", False)

        self._controller_config = AgentControllerConfig(
            provider_configs=self._provider_configs,
            provider_config=self._provider_config,
            provider_slug=self._provider_slug,
            model_slug=self._model_slug,
            system_message=self._config.get("system_message", "You are a helpful assistant."),
            tools=tools,
            stream=True if self._config.get("stream") is None else self._config.get("stream"),
            realtime=self._realtime,
            max_steps=min(self._config.get("max_steps", 30), 100),
            metadata=metadata,
        )

        super().__init__(
            coordinator_urn=coordinator_urn,
            dependencies=dependencies,
            templates=templates,
            bookkeeping_queue=bookkeeping_queue,
        )

    def _add_error_from_tool_call(self, output_index, tool_name, tool_call_id, errors):
        error_message = "\n".join([error for error in errors])
        self._stitched_data = stitch_model_objects(
            self._stitched_data,
            {
                "agent": {
                    output_index: AgentControllerData(
                        type=AgentControllerDataType.TOOL_CALLS,
                        data=AgentToolCallsMessage(responses={tool_call_id: f"Error: {error_message}"}),
                    )
                },
            },
        )

        delta = self._dmp.to_delta("", error_message)

        self._content_queue.put_nowait(
            {
                "deltas": {f"agent_tool_call_errors__{output_index}__{tool_name}__{tool_call_id}": delta},
                "chunk": {f"{tool_name}/{output_index}/{tool_call_id}": errors},
            }
        )
        self._agent_outputs[f"agent_tool_call_errors__{output_index}__{tool_name}__{tool_call_id}"] = error_message

        if len(self._stitched_data["agent"][output_index].data.tool_calls) == len(
            self._stitched_data["agent"][output_index].data.responses.keys()
        ):
            self._agent_controller.process(
                AgentControllerData(
                    type=AgentControllerDataType.TOOL_CALLS,
                    data=AgentToolCallsMessage(
                        tool_calls=self._stitched_data["agent"][output_index].data.tool_calls,
                        responses=self._stitched_data["agent"][output_index].data.responses,
                    ),
                )
            )

    async def _process_output(self):
        message_index = 0

        while True:
            try:
                controller_output = self._agent_output_queue.get_nowait()

                if controller_output.type == AgentControllerDataType.AGENT_OUTPUT:
                    self._stitched_data["agent"][message_index] = stitch_model_objects(
                        self._stitched_data["agent"].get(message_index, None),
                        controller_output,
                    )

                    old_agent_output = self._agent_outputs.get(f"agent_output__{message_index}", "")
                    self._agent_outputs[f"agent_output__{message_index}"] = (
                        self._stitched_data["agent"][message_index].data.content[0].data
                    )
                    delta = self._dmp.to_delta(old_agent_output, self._agent_outputs[f"agent_output__{message_index}"])

                    self._content_queue.put_nowait(
                        {
                            "deltas": {f"agent_output__{message_index}": delta},
                            "chunk": {"agent": {message_index: controller_output}},
                        }
                    )

                elif controller_output.type == AgentControllerDataType.AGENT_OUTPUT_END:
                    self._content_queue.put_nowait(
                        {
                            "output": {
                                **self._agent_outputs,
                                "output": self._stitched_data["agent"][message_index].data.content[0].data,
                            },
                            "chunks": self._stitched_data,
                        }
                    )

                elif controller_output.type == AgentControllerDataType.TOOL_CALLS:
                    self._stitched_data["agent"][message_index] = stitch_model_objects(
                        self._stitched_data["agent"].get(message_index, None),
                        controller_output,
                    )
                    deltas = {}

                    for tool_call_index, tool_call in enumerate(controller_output.data.tool_calls):
                        stitched_tool_call = self._stitched_data["agent"][message_index].data.tool_calls[
                            tool_call_index
                        ]

                        old_tool_call_data = self._agent_outputs.get(
                            f"agent_tool_calls__{message_index}__{stitched_tool_call.name}__{stitched_tool_call.id}",
                            "",
                        )
                        self._agent_outputs[
                            f"agent_tool_calls__{message_index}__{stitched_tool_call.name}__{stitched_tool_call.id}"
                        ] = stitched_tool_call.arguments

                        delta = self._dmp.to_delta(old_tool_call_data, stitched_tool_call.arguments)
                        deltas[
                            f"agent_tool_calls__{message_index}__{stitched_tool_call.name}__{stitched_tool_call.id}"
                        ] = delta

                    self._content_queue.put_nowait(
                        {
                            "deltas": deltas,
                            "chunk": {"agent": {message_index: controller_output}},
                        }
                    )

                elif controller_output.type == AgentControllerDataType.TOOL_CALLS_END:
                    tool_calls = self._stitched_data["agent"][message_index].data.tool_calls

                    for tool_call in tool_calls:
                        tool_call_args = tool_call.arguments
                        try:
                            tool_call_args = json.loads(tool_call_args)
                            tool_call_args["_inputs0"] = self._messages["_inputs0"]
                        except Exception:
                            pass

                        try:
                            (
                                await self._output_stream.write_raw(
                                    Message(
                                        id=f"{message_index}/{tool_call.id}",
                                        type=MessageType.CONTENT,
                                        sender=f"{tool_call.name}/{message_index}/{tool_call.id}",
                                        receiver=f"{tool_call.name}/{message_index}/{tool_call.id}",
                                        data=ContentData(content=tool_call_args),
                                    )
                                )
                            ).get()
                        except Exception as e:
                            self._add_error_from_tool_call(message_index, tool_call.name, tool_call.id, [str(e)])
                elif controller_output.type == AgentControllerDataType.ERROR:
                    # Treat this as an agent output end
                    self._errors = [Error(message=controller_output.data.content[0].data)]
                elif controller_output.type == AgentControllerDataType.INPUT_STREAM:
                    # Input has started streaming. We need to let the client know so they can interrupt audio playback
                    self._content_queue.put_nowait(
                        {
                            "deltas": {"agent_input_audio_stream_started_at": self._dmp.to_delta("", str(time.time()))},
                        }
                    )
                elif controller_output.type == AgentControllerDataType.OUTPUT_STREAM:
                    # Send output_stream info to the client
                    for content in controller_output.data.content:
                        if content.type == AgentMessageContentType.AUDIO_STREAM:
                            self._content_queue.put_nowait(
                                {
                                    "deltas": {
                                        f"agent_output_audio_stream__{message_index}": self._dmp.to_delta(
                                            "", content.data
                                        )
                                    },
                                }
                            )
                        elif content.type == AgentMessageContentType.TRANSCRIPT_STREAM:
                            self._content_queue.put_nowait(
                                {
                                    "deltas": {
                                        f"agent_output_transcript_stream__{message_index}": self._dmp.to_delta(
                                            "", content.data
                                        )
                                    },
                                }
                            )

                if controller_output.type == AgentControllerDataType.TOOL_CALLS_END:
                    message_index += 1
                elif controller_output.type == AgentControllerDataType.AGENT_OUTPUT_END:
                    message_index = 0
                elif controller_output.type == AgentControllerDataType.USAGE_DATA:
                    self._usage_data = {
                        "usage_metrics": [
                            [
                                ("promptly/*/*/*", MetricType.INVOCATION, (ProviderConfigSource.PLATFORM_DEFAULT, 1)),
                                (
                                    f"{self._provider_slug}/*/{self._model_slug}/*",
                                    MetricType.INPUT_TOKENS,
                                    (
                                        self._provider_config.provider_config_source,
                                        controller_output.data.prompt_tokens,
                                    ),
                                ),
                                (
                                    f"{self._provider_slug}/*/{self._model_slug}/*",
                                    MetricType.OUTPUT_TOKENS,
                                    (
                                        self._provider_config.provider_config_source,
                                        controller_output.data.completion_tokens,
                                    ),
                                ),
                            ]
                        ]
                    }

                self._output_stream.bookkeep(
                    BookKeepingData(
                        output=self._stitched_data["agent"],
                        config=self._config,
                        usage_data=self._usage_data,
                    )
                )
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.exception(f"Error processing controller output: {e}")

    def on_receive(self, message: Message) -> None:
        if message.type == MessageType.CONTENT:
            if message.sender == "_inputs0":
                if self._realtime:
                    # For realtime, we send both text and audio streams if available
                    content = []
                    if message.data.content.get("text", None):
                        content.append(
                            AgentMessageContent(
                                type=AgentMessageContentType.TEXT_STREAM, data=message.data.content.get("text")
                            )
                        )
                        self._content_queue.put_nowait(
                            {
                                "deltas": {
                                    "agent_input_text_stream": self._dmp.to_delta(
                                        "", message.data.content.get("text").objref
                                    )
                                },
                            }
                        )
                    if message.data.content.get("audio", None):
                        content.append(
                            AgentMessageContent(
                                type=AgentMessageContentType.AUDIO_STREAM, data=message.data.content.get("audio")
                            )
                        )
                        self._content_queue.put_nowait(
                            {
                                "deltas": {
                                    "agent_input_audio_stream": self._dmp.to_delta(
                                        "", message.data.content.get("audio").objref
                                    )
                                },
                            }
                        )
                    if message.data.content.get("transcript", None):
                        content.append(
                            AgentMessageContent(
                                type=AgentMessageContentType.TRANSCRIPT_STREAM,
                                data=message.data.content.get("transcript"),
                            )
                        )
                        self._content_queue.put_nowait(
                            {
                                "deltas": {
                                    "agent_input_transcript_stream": self._dmp.to_delta(
                                        "", message.data.content.get("transcript").objref
                                    )
                                },
                            }
                        )

                    content.append(
                        AgentMessageContent(
                            type=AgentMessageContentType.METADATA,
                            data=message.data.content.get("metadata", {}),
                        )
                    )

                    self._agent_controller.process(
                        AgentControllerData(
                            type=AgentControllerDataType.INPUT_STREAM,
                            data=AgentUserMessage(
                                content=content,
                            ),
                        )
                    )
                else:
                    # Get and hydrate user_message_template with message.data
                    user_message_template = self._config.get("user_message")

                    try:
                        user_message = (
                            render_template(user_message_template, message.data.content)
                            if user_message_template
                            else json.dumps(message.data.content)
                        )
                    except Exception as e:
                        logger.error(f"Error rendering user message template: {e}")
                        user_message = user_message_template

                    self._agent_controller.process(
                        AgentControllerData(
                            type=AgentControllerDataType.INPUT,
                            data=AgentUserMessage(
                                content=[AgentMessageContent(type=AgentMessageContentType.TEXT, data=user_message)]
                            ),
                        )
                    )
            elif message.sender != message.receiver:
                tool_name = message.sender.split("/")[0]
                output_index = int(message.sender.split("/")[1])
                tool_call_id = message.sender.split("/")[2]

                template = self._templates.get(tool_name, None)
                tool_call_output = render_template(template, message.data.content)

                self._stitched_data = stitch_model_objects(
                    self._stitched_data,
                    {
                        "agent": {
                            output_index: AgentControllerData(
                                type=AgentControllerDataType.TOOL_CALLS,
                                data=AgentToolCallsMessage(responses={tool_call_id: tool_call_output}),
                            )
                        },
                    },
                )

                self._content_queue.put_nowait(
                    {
                        "deltas": {f"agent_tool_call_done__{output_index}__{tool_name}__{tool_call_id}": "True"},
                    }
                )

                if len(self._stitched_data["agent"][output_index].data.tool_calls) == len(
                    self._stitched_data["agent"][output_index].data.responses.keys()
                ):
                    self._agent_controller.process(
                        AgentControllerData(
                            type=AgentControllerDataType.TOOL_CALLS,
                            data=AgentToolCallsMessage(
                                tool_calls=self._stitched_data["agent"][output_index].data.tool_calls,
                                responses=self._stitched_data["agent"][output_index].data.responses,
                            ),
                        )
                    )
        elif (
            message.type == MessageType.CONTENT_STREAM_CHUNK or message.type == MessageType.ERRORS
        ) and message.sender != "_inputs0":
            tool_name = message.sender.split("/")[0]
            output_index = int(message.sender.split("/")[1])
            tool_call_id = message.sender.split("/")[2]

            if message.type == MessageType.CONTENT_STREAM_CHUNK:
                self._stitched_data = stitch_model_objects(
                    self._stitched_data,
                    {message.sender: message.data.chunk},
                )

                # Render the tool call output
                template = self._templates.get(tool_name, None)
                tool_call_output = render_template(template, self._stitched_data[message.sender])

                prev_tool_call_output = self._agent_outputs.get(
                    f"agent_tool_call_output__{output_index}__{tool_name}__{tool_call_id}",
                    "",
                )
                self._agent_outputs[
                    f"agent_tool_call_output__{output_index}__{tool_name}__{tool_call_id}"
                ] = tool_call_output

                delta = self._dmp.to_delta(prev_tool_call_output, tool_call_output)

                self._content_queue.put_nowait(
                    {
                        "deltas": {f"agent_tool_call_output__{output_index}__{tool_name}__{tool_call_id}": delta},
                        "chunk": {message.sender: message.data.chunk},
                    }
                )
            else:
                self._add_error_from_tool_call(
                    output_index, tool_name, tool_call_id, [error.message for error in message.data.errors]
                )
        elif message.type == MessageType.CONTENT_STREAM_BEGIN:
            if message.sender != "_inputs0":
                return
        elif message.type == MessageType.CONTENT_STREAM_END:
            if message.sender != "_inputs0":
                return

    def reset(self):
        super().reset()
        self._usage_data = {}
        self._stitched_data = {"agent": {}}
        self._agent_outputs = {}

        if self._process_output_task:
            self._process_output_task.cancel()
            self._process_output_task = None

        self._agent_output_queue = asyncio.Queue()
        self._agent_controller = AgentController(self._agent_output_queue, self._controller_config)

        # If there is no running event loop, create one and run the task
        try:
            loop = asyncio.get_running_loop()
            logger.info("Running process output task in existing event loop")
            self._process_output_task = loop.create_task(self._process_output())
        except RuntimeError:
            logger.info("No running event loop, creating one and running process output task")
            self._process_output_task = run_coro_in_new_loop(self._process_output())

    def on_stop(self):
        super().on_stop()
        if self._process_output_task:
            self._process_output_task.cancel()
            self._process_output_task = None

        self._agent_controller.terminate()
