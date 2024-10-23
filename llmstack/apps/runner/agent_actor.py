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
from llmstack.play.messages import ContentData, Error, Message, MessageType
from llmstack.play.output_stream import stitch_model_objects
from llmstack.play.utils import run_coro_in_new_loop

logger = logging.getLogger(__name__)


class AgentActor(OutputActor):
    def __init__(
        self,
        coordinator_urn,
        dependencies,
        templates: Dict[str, str] = {},
        agent_config: Dict[str, Any] = {},
        provider_configs: Dict[str, Any] = {},
        tools: List[Dict] = [],
    ):
        self._process_output_task = None
        self._config = agent_config
        self._provider_configs = provider_configs

        self._controller_config = AgentControllerConfig(
            provider_configs=self._provider_configs,
            provider_slug=self._config.get("provider_slug", "openai"),
            model_slug=self._config.get("model", "gpt-4o-mini"),
            system_message=self._config.get("system_message", "You are a helpful assistant."),
            tools=tools,
            stream=True if self._config.get("stream") is None else self._config.get("stream"),
            realtime=self._config.get("realtime", False),
            max_steps=min(self._config.get("max_steps", 30), 100),
        )

        super().__init__(
            coordinator_urn=coordinator_urn,
            dependencies=dependencies,
            templates=templates,
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

        delta = self._diff_match_patch.diff_toDelta(self._diff_match_patch.diff_main("", error_message))

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
                    delta = self._diff_match_patch.diff_toDelta(
                        self._diff_match_patch.diff_main(
                            old_agent_output, self._agent_outputs[f"agent_output__{message_index}"]
                        )
                    )

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
                    self._bookkeeping_data_map["agent"] = self._stitched_data["agent"]
                    self._bookkeeping_data_map["agent"]["timestamp"] = time.time()
                    self._bookkeeping_data_future.set(self._bookkeeping_data_map)
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

                        delta = self._diff_match_patch.diff_toDelta(
                            self._diff_match_patch.diff_main(old_tool_call_data, stitched_tool_call.arguments)
                        )
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

                if controller_output.type == AgentControllerDataType.TOOL_CALLS_END:
                    message_index += 1
                elif controller_output.type == AgentControllerDataType.AGENT_OUTPUT_END:
                    message_index = 0
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.exception(f"Error processing controller output: {e}")

    def on_receive(self, message: Message) -> None:
        if message.type == MessageType.CONTENT:
            if message.sender == "_inputs0":
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

                # Begin processing input
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

                delta = self._diff_match_patch.diff_toDelta(
                    self._diff_match_patch.diff_main(prev_tool_call_output, tool_call_output)
                )

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
        elif message.type == MessageType.BOOKKEEPING:
            self._bookkeeping_data_map[message.sender] = message.data

    def reset(self):
        super().reset()
        self._stitched_data = {"agent": {}}
        self._agent_outputs = {}

        if self._process_output_task:
            self._process_output_task.cancel()
            self._process_output_task = None

        self._agent_output_queue = asyncio.Queue()
        self._agent_controller = AgentController(self._agent_output_queue, self._controller_config)

        # If there is no running event loop, create one and run the task
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.info("No running event loop, creating one and running process output task")
            run_coro_in_new_loop(self._process_output())
        else:
            logger.info("Running process output task")
            self._process_output_task = asyncio.create_task(self._process_output())
