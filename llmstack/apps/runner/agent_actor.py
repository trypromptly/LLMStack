import asyncio
import json
import logging
from types import TracebackType
from typing import Any, Dict, List

from pydantic import BaseModel

from llmstack.apps.runner.agent_controller import (
    AgentController,
    AgentControllerConfig,
    AgentControllerData,
    AgentControllerDataType,
)
from llmstack.common.utils.liquid import render_template
from llmstack.play.actor import Actor, BookKeepingData
from llmstack.play.messages import Message, MessageType, ToolCallData
from llmstack.play.utils import run_coro_in_new_loop

logger = logging.getLogger(__name__)


class AgentToolCall(BaseModel):
    id: str
    name: str
    arguments: str


class AgentOutput(BaseModel):
    content: str
    tool_calls: List[AgentToolCall] = []


class AgentActor(Actor):
    def __init__(
        self,
        coordinator_urn,
        dependencies=["input"],
        config: Dict[str, Any] = {},
        provider_configs: Dict[str, Any] = {},
        tools: List[Dict] = [],
    ):
        super().__init__(id="agent", coordinator_urn=coordinator_urn, dependencies=dependencies, output_cls=AgentOutput)

        self._process_output_task = None
        self._config = config
        self._provider_configs = provider_configs

        self._controller_config = AgentControllerConfig(
            provider_configs=self._provider_configs,
            provider_slug=self._config.get("provider_slug", "openai"),
            model_slug=self._config.get("model", "gpt-4o-mini"),
            system_message=self._config.get("system_message", "You are a helpful assistant."),
            tools=tools,
            stream=self._config.get("stream", True) or True,
            realtime=self._config.get("realtime", False),
        )

    async def _process_output(self):
        while True:
            try:
                controller_output = self._agent_output_queue.get_nowait()
                if controller_output.type == AgentControllerDataType.TOOL_CALL:
                    try:
                        await self._output_stream.write_raw(
                            Message(
                                id=controller_output.data.id,
                                type=MessageType.TOOL_CALL,
                                sender="agent",
                                receiver=f"{controller_output.data.function.name}/{controller_output.data.id}",
                                data=ToolCallData(
                                    tool_call_id=controller_output.data.id,
                                    input={},  # TODO: Add input from processor
                                    name=controller_output.data.function.name,
                                    arguments=json.loads(controller_output.data.function.arguments),
                                ),
                            )
                        )
                    except Exception as e:
                        logger.exception(f"Error sending tool call: {e}")
                elif controller_output.type == AgentControllerDataType.OUTPUT:
                    await self._output_stream.write(
                        AgentOutput(
                            content=controller_output.data.get("content", ""),
                            tool_calls=controller_output.data.get("tool_calls", []),
                        )
                    )
                elif controller_output.type == AgentControllerDataType.END:
                    self._output_stream.finalize()

                    # Send bookkeeping data
                    self._output_stream.bookkeep(BookKeepingData(config=self._controller_config.model_dump()))
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.exception(f"Error processing controller output: {e}")

    def on_receive(self, message: Message) -> None:
        if message.type == MessageType.CONTENT:
            if message.sender == "input":
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
                    AgentControllerData(type=AgentControllerDataType.INPUT, data=user_message)
                )
        elif message.type == MessageType.TOOL_CALL_RESPONSE:
            # Relay message to agent controller
            self._agent_controller.process(
                AgentControllerData(
                    type=AgentControllerDataType.TOOL_CALL_RESPONSE,
                    data={
                        "tool_call_id": message.data.tool_call_id,
                        "output": message.data.output,
                    },
                )
            )

    def on_failure(
        self, exception_type: type[BaseException], exception_value: BaseException, traceback: TracebackType
    ) -> None:
        return super().on_failure(exception_type, exception_value, traceback)

    def on_stop(self):
        pass

    def reset(self):
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
