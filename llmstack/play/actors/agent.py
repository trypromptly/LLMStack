import logging
import time
import uuid
from typing import Any

import orjson as json
from asgiref.sync import async_to_sync
from openai import OpenAI
from pydantic import BaseModel

from llmstack.apps.app_session_utils import save_agent_app_session_data
from llmstack.apps.types.agent import AgentModel
from llmstack.common.utils.liquid import render_template
from llmstack.common.utils.provider_config import get_matched_provider_config
from llmstack.play.actor import Actor, BookKeepingData
from llmstack.play.actors.output import OutputResponse
from llmstack.play.output_stream import Message, MessageType
from llmstack.processors.providers.config import ProviderConfigSource
from llmstack.processors.providers.metrics import MetricType

logger = logging.getLogger(__name__)


class ToolInvokeInput(BaseModel):
    """
    Data to invoke a tool
    """

    input: dict = {}
    tool_name: str = ""
    tool_args: dict = {}


class FunctionCall(BaseModel):
    """
    Data for a function call
    """

    name: str = ""
    arguments: str = ""
    output: Any = ""


class AgentOutput(BaseModel):
    """
    Output from the agent
    """

    id: str = ""  # Unique ID for the output
    content: Any = ""  # Content of the output
    from_id: str = ""  # ID of the actor that produced the output
    type: str = "step"  # Type of output
    done: bool = False  # Whether the output is done


class AgentActor(Actor):
    def __init__(
        self,
        output_stream,
        processor_configs,
        dependencies=[],
        all_dependencies=[],
        **kwargs,
    ):
        super().__init__(dependencies=dependencies, all_dependencies=all_dependencies)
        self._processor_configs = processor_configs
        self._output_stream = output_stream
        self._functions = kwargs.get("functions")
        self._id = kwargs.get("id")
        self._env = kwargs.get("env")
        self._input = kwargs.get("input")
        self._config = kwargs.get("config", {})
        self._agent_app_session_data = kwargs.get("agent_app_session_data")
        self._system_message = [
            {
                "role": "system",
                "content": self._config.get(
                    "system_message",
                    "You are a helpful assistant that uses provided tools to perform actions.",
                ),
            },
        ]
        self._provider_config = None

        if "data" in self._agent_app_session_data and "chat_history" in self._agent_app_session_data["data"]:
            self._chat_history = self._agent_app_session_data["data"]["chat_history"]
        else:
            self._chat_history = []

        openai_provider_config = get_matched_provider_config(
            provider_configs=self._env.get("provider_configs", {}),
            provider_slug="openai",
            model_slug=self._config.get("model", "gpt-3.5-turbo"),
        )
        self._provider_config = openai_provider_config

        self._openai_client = OpenAI(
            api_key=openai_provider_config.api_key,
            base_url=openai_provider_config.base_url,
        )
        self._stream = self._config.get("stream")
        if self._stream is None:
            self._stream = (
                True
                if self._config.get("model", "gpt-3.5-turbo") in list(map(lambda x: str(x.value), AgentModel))
                else False
            )

        self._agent_messages = []
        self._tool_calls = []
        self._tool_call_outputs = []
        self._usage_data = [("promptly/*/*/*", MetricType.INVOCATION, (ProviderConfigSource.PLATFORM_DEFAULT, 1))]

        if "chat_history_limit" in self._config and self._config["chat_history_limit"] > 0:
            self._chat_history_limit = self._config["chat_history_limit"]
            self._agent_messages += self._chat_history[-self._chat_history_limit :]  # noqa: E203
        else:
            self._chat_history_limit = 0

        # Get and hydrate user_message_template with self._input
        user_message_template = self._config.get("user_message")

        try:
            user_message = (
                render_template(user_message_template, self._input)
                if user_message_template
                else json.dumps(self._input).decode("utf-8")
            )

            # Hydrate system_message_template with self._input
            if self._system_message and len(self._system_message) > 0 and "content" in self._system_message[0]:
                self._system_message[0]["content"] = render_template(self._system_message[0]["content"], self._input)
        except Exception as e:
            logger.error(f"Error rendering user message template: {e}")
            user_message = user_message_template

        self._agent_messages.append(
            {
                "role": "user",
                "content": user_message,
            },
        )

        self._base_price_per_message = 100
        configured_model = self._config.get("model")
        if configured_model == "gpt-4o-mini":
            self._base_price_per_message = 20
        elif configured_model == "gpt-4o":
            self._base_price_per_message = 200
        elif configured_model == "gpt-4-32k":
            self._base_price_per_message = 500
        elif configured_model == "gpt-4":
            self._base_price_per_message = 300
        elif configured_model == "gpt-4-turbo-latest":
            self._base_price_per_message = 300
        elif configured_model == "gpt-4-turbo":
            self._base_price_per_message = 300
        elif configured_model == "o1-mini":
            self._base_price_per_message = 200
        elif configured_model == "o1-preview":
            self._base_price_per_message = 1000
        else:
            self._base_price_per_message = 150

    def run(self) -> None:
        # This will send a message to itself to start the loop
        self.actor_ref.tell(
            Message(
                message_type=MessageType.BEGIN,
                message=None,
                message_to=self._id,
            ),
        )

    def _on_error(self, message) -> None:
        async_to_sync(self._output_stream.write)(
            AgentOutput(
                content=message.message,
                from_id=message.message_from,
                id=message.message_id or str(uuid.uuid4()),
                type="step_error",
            ),
        )
        output_response = OutputResponse(
            response_content_type="text/markdown",
            response_status=400,
            response_body=message.message,
            response_headers={},
        )
        bookkeeping_data = BookKeepingData(
            run_data={
                **output_response._asdict(),
            },
            input=self._input,
            config={},
            output={
                "agent_messages": self._agent_messages,
            },
            timestamp=time.time(),
            usage_data={
                "credits": self._base_price_per_message * len(self._agent_messages),
                "usage_metrics": self._usage_data,
            },
        )
        self._output_stream.bookkeep(bookkeeping_data)
        async_to_sync(self._output_stream.write_raw)(
            Message(
                message_type=MessageType.AGENT_DONE,
                message_from="agent",
            ),
        )

    def on_receive(self, message: Message) -> Any:
        max_steps = self._config.get("max_steps", 10) + 2

        if len(self._agent_messages) > max_steps + self._config.get("chat_history_limit", 0):
            output_response = OutputResponse(
                response_content_type="text/markdown",
                response_status=200,
                response_body="Exceeded max steps. Terminating.",
                response_headers={},
            )
            bookkeeping_data = BookKeepingData(
                run_data={
                    **output_response._asdict(),
                },
                input=self._input,
                config={},
                output={
                    "agent_messages": self._agent_messages,
                },
                timestamp=time.time(),
                usage_data={
                    "credits": self._base_price_per_message * len(self._agent_messages),
                    "usage_metrics": self._usage_data,
                },
            )
            self._output_stream.bookkeep(bookkeeping_data)

            async_to_sync(self._output_stream.write_raw)(
                Message(
                    message_type=MessageType.AGENT_DONE,
                    message_from="agent",
                ),
            )
            return

        if message.message_type == MessageType.BEGIN and message.message_to == self._id:
            logger.info(f"Agent actor {self.actor_urn} started")

            model = self._config.get("model", "gpt-3.5-turbo")

            if model == "gpt-3.5-turbo-latest":
                model = "gpt-3.5-turbo"
            elif model == "gpt-4-turbo-latest":
                model = "gpt-4-turbo"

            # Make one call to the model
            full_content = ""
            function_name = ""
            function_args = ""
            finish_reason = None
            self._tool_calls = []
            self._tool_call_outputs = []
            result = self._openai_client.chat.completions.create(
                model=model,
                messages=self._system_message + self._agent_messages,
                stream=self._stream,
                tools=[{"type": "function", "function": x} for x in self._functions] if self._functions else None,
                seed=self._config.get("seed", None),
                temperature=self._config.get("temperature", 0.7),
                stream_options={"include_usage": True} if self._stream else None,
            )
            agent_message_id = str(uuid.uuid4())
            agent_function_call_id = None

            for data in result if self._stream else [result]:
                if data.usage:
                    self._usage_data.append(
                        (
                            f"openai/*/{model}/*",
                            MetricType.INPUT_TOKENS,
                            (self._provider_config.provider_config_source, data.usage.prompt_tokens),
                        )
                    )
                    self._usage_data.append(
                        (
                            f"openai/*/{model}/*",
                            MetricType.OUTPUT_TOKENS,
                            (self._provider_config.provider_config_source, data.usage.completion_tokens),
                        )
                    )
                if (
                    data.object == "chat.completion.chunk"
                    and len(
                        data.choices,
                    )
                    > 0
                    and data.choices[0].delta
                ) or (
                    data.object == "chat.completion"
                    and len(
                        data.choices,
                    )
                    > 0
                ):
                    finish_reason = data.choices[0].finish_reason
                    delta = data.choices[0].delta if data.object == "chat.completion.chunk" else data.choices[0].message
                    function_call = delta.function_call
                    tool_calls_chunk = delta.tool_calls
                    content = delta.content

                    if function_call and function_call.name:
                        function_name += function_call.name
                        agent_function_call_id = str(uuid.uuid4())
                        async_to_sync(self._output_stream.write)(
                            AgentOutput(
                                content=FunctionCall(
                                    name=function_call.name,
                                ),
                                id=f"{agent_message_id}/{agent_function_call_id}",
                                from_id=function_name,
                                type="step",
                            ),
                        )
                    elif function_call and function_call.arguments:
                        function_args += function_call.arguments
                        async_to_sync(self._output_stream.write)(
                            AgentOutput(
                                content=FunctionCall(
                                    arguments=function_call.arguments,
                                ),
                                id=f"{agent_message_id}/{agent_function_call_id}",
                                from_id=function_name,
                                type="step",
                            ),
                        )
                    elif tool_calls_chunk and len(tool_calls_chunk) > 0:
                        tool_call_index = 0
                        for tool_call in tool_calls_chunk:
                            if hasattr(tool_call, "index"):
                                tool_call_index = tool_call.index

                            if len(self._tool_calls) < tool_call_index + 1:
                                # Insert at the index
                                self._tool_calls.insert(
                                    tool_call_index,
                                    {
                                        "id": tool_call.id,
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments,
                                    },
                                )
                                async_to_sync(self._output_stream.write)(
                                    AgentOutput(
                                        content=FunctionCall(
                                            name=tool_call.function.name,
                                            arguments=tool_call.function.arguments or "",
                                        ),
                                        id=tool_call.id,
                                        from_id=tool_call.function.name,
                                        type="step",
                                    ),
                                )

                                if not hasattr(tool_call, "index"):
                                    tool_call_index += 1
                            else:
                                # Update at the index
                                self._tool_calls[tool_call_index]["arguments"] += tool_call.function.arguments
                                async_to_sync(self._output_stream.write)(
                                    AgentOutput(
                                        content=FunctionCall(
                                            arguments=tool_call.function.arguments,
                                        ),
                                        id=self._tool_calls[tool_call_index]["id"],
                                        from_id=self._tool_calls[tool_call_index]["name"],
                                        type="step",
                                    ),
                                )
                    elif content:
                        full_content += content
                        async_to_sync(self._output_stream.write)(
                            AgentOutput(
                                content=content,
                                id=agent_message_id,
                                from_id="agent",
                                type="output",
                            ),
                        )

            if function_name and finish_reason == "function_call":
                logger.info(
                    f"Agent function call: {function_name}({function_args})",
                )

                self._agent_messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": function_name,
                            "arguments": function_args,
                        },
                    },
                )

                try:
                    tool_invoke_input = ToolInvokeInput(
                        input=self._input,
                        tool_name=function_name,
                        tool_args=json.loads(function_args),
                    )
                    async_to_sync(self._output_stream.write_raw)(
                        Message(
                            message_id=f"{agent_message_id}/{agent_function_call_id}",
                            message_type=MessageType.TOOL_INVOKE,
                            message=tool_invoke_input,
                            message_to=function_name,
                            message_from=self._id,
                        ),
                    )
                except Exception as e:
                    logger.error(f"Error invoking tool {function_name}: {e}")
                    self._on_error(
                        Message(
                            message_from="agent",
                            message=f"Error invoking tool {function_name}: {e}",
                        ),
                    )
            elif len(self._tool_calls) > 0 and (finish_reason == "tool_calls" or finish_reason == "stop"):
                logger.info(f"Agent tool calls: {self._tool_calls}")

                self._agent_messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": x["id"],
                                "type": "function",
                                "function": {
                                    "name": x["name"],
                                    "arguments": x["arguments"],
                                },
                            }
                            for x in self._tool_calls
                        ],
                    },
                )

                for tool_call in self._tool_calls:
                    try:
                        tool_invoke_input = ToolInvokeInput(
                            input=self._input,
                            tool_name=tool_call["name"],
                            tool_args=json.loads(tool_call["arguments"]),
                        )
                        async_to_sync(self._output_stream.write_raw)(
                            Message(
                                message_id=tool_call["id"],
                                message_type=MessageType.TOOL_INVOKE,
                                message=tool_invoke_input,
                                message_to=tool_call["name"],
                                message_from=self._id,
                            ),
                        )
                    except Exception as e:
                        logger.error(f"Error invoking tool {tool_call['name']}: {e}")
                        self._on_error(
                            Message(
                                message_from="agent",
                                message=f"Error invoking tool {tool_call['name']}: {e}",
                            ),
                        )
            elif full_content and finish_reason == "stop":
                output_response = OutputResponse(
                    response_content_type="text/markdown",
                    response_status=200,
                    response_body=full_content,
                    response_headers={},
                )
                bookkeeping_data = BookKeepingData(
                    run_data={
                        **output_response._asdict(),
                    },
                    input=self._input,
                    config={},
                    output={
                        "agent_messages": self._agent_messages,
                    },
                    timestamp=time.time(),
                    usage_data={
                        "credits": self._base_price_per_message * len(self._agent_messages),
                        "usage_metrics": self._usage_data,
                    },
                )
                # Persist session data
                self._agent_app_session_data["data"] = {
                    "chat_history": self._chat_history[: -self._chat_history_limit]
                    + self._agent_messages
                    + [{"role": "assistant", "content": full_content}],
                }
                save_agent_app_session_data(self._agent_app_session_data)

                self._output_stream.bookkeep(bookkeeping_data)
                self._output_stream.finalize()

                async_to_sync(self._output_stream.write_raw)(
                    Message(
                        message_type=MessageType.AGENT_DONE,
                        message_from="agent",
                    ),
                )

        if message.message_type == MessageType.STREAM_DATA:
            if message.message_from in self._processor_configs:
                async_to_sync(self._output_stream.write)(
                    AgentOutput(
                        content=FunctionCall(
                            output=message.message,
                        ),
                        from_id=message.message_from,
                        id=message.response_to,
                        type="step",
                        done=True,
                    ),
                )

        if message.message_type == MessageType.STREAM_CLOSED:
            # Get the output from the processor invoke and resume the loop
            try:
                processor_template = self._processor_configs[message.message_from]["processor"]["output_template"]

                processor_output = render_template(
                    processor_template["markdown"],
                    message.message,
                )

                function_response = {}
                if message.response_to and message.response_to.startswith("call_"):
                    function_response = {
                        "role": "tool",
                        "tool_call_id": message.response_to,
                        "name": message.message_from,
                        "content": processor_output,
                    }
                else:
                    function_response = {
                        "role": "function",
                        "content": processor_output,
                        "name": message.message_from,
                    }

                self._agent_messages.append(function_response)
                self._tool_call_outputs.append(function_response)

                if len(self._tool_calls) == len(self._tool_call_outputs):
                    self._tool_calls = []
                    self._tool_call_outputs = []
                    self.actor_ref.tell(
                        Message(
                            message_type=MessageType.BEGIN,
                            message=None,
                            message_to=self._id,
                        ),
                    )
            except Exception as e:
                logger.error(f"Error getting tool output: {e}")

        if message.message_type == MessageType.STREAM_ERROR:
            # Log the error and quit for now
            self._on_error(message)

    def on_stop(self) -> None:
        super().on_stop()

    def get_dependencies(self):
        return list(
            set([x["template_key"] for x in self._processor_configs.values()]),
        )
