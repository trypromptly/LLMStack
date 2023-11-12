import logging
import time
import uuid
from typing import Any

import orjson as json
from asgiref.sync import async_to_sync
from jinja2 import Template
from openai import OpenAI
from pydantic import BaseModel

from llmstack.play.actor import Actor, BookKeepingData
from llmstack.play.actors.output import OutputResponse
from llmstack.play.output_stream import Message, MessageType

logger = logging.getLogger(__name__)


class ToolInvokeInput(BaseModel):
    """
    Data to invoke a tool
    """
    input: dict = {}
    tool_name: str = ''
    tool_args: dict = {}


class FunctionCall(BaseModel):
    """
    Data for a function call
    """
    name: str = ''
    arguments: str = ''
    output: Any = ''


class AgentOutput(BaseModel):
    """
    Output from the agent
    """
    id: str = ''  # Unique ID for the output
    content: Any = ''  # Content of the output
    from_id: str = ''  # ID of the actor that produced the output
    type: str = 'step'  # Type of output


class AgentActor(Actor):
    def __init__(self, output_stream, processor_configs, dependencies=[], all_dependencies=[], **kwargs):
        super().__init__(dependencies=dependencies, all_dependencies=all_dependencies)
        self._processor_configs = processor_configs
        self._output_stream = output_stream
        self._functions = kwargs.get('functions')
        self._id = kwargs.get('id')
        self._env = kwargs.get('env')
        self._input = kwargs.get('input')
        self._config = kwargs.get('config', {})

        self._openai_client = OpenAI(
            api_key=self._env['openai_api_key']
        )

        self._agent_messages = [{
            'role': 'system',
            'content': self._config.get('system_message', 'You are a helpful assistant that uses provided tools to perform actions.')
        }, {
            'role': 'user',
            'content': self._input.get('task', 'Hello')
        }]

    # This will send a message to itself to start the loop
    def run(self) -> None:
        self.actor_ref.tell(
            Message(message_type=MessageType.BEGIN, message=None, message_to=self._id))

    def _on_error(self, message) -> None:
        async_to_sync(self._output_stream.write)(
            AgentOutput(
                content=message.message,
                from_id=message.message_from,
                id=message.message_id or str(uuid.uuid4()),
                type='step_error',
            )
        )
        output_response = OutputResponse(
            response_content_type='text/markdown',
            response_status=400,
            response_body=message.message,
            response_headers={},
        )
        bookkeeping_data = BookKeepingData(
            run_data={**output_response._asdict()}, input=self._input, config={}, output={'agent_messages': self._agent_messages}, timestamp=time.time(),
        )
        self._output_stream.bookkeep(bookkeeping_data)
        async_to_sync(self._output_stream.write_raw)(
            Message(
                message_type=MessageType.AGENT_DONE,
                message_from='agent',
            )
        )

    def on_receive(self, message: Message) -> Any:
        max_steps = self._config.get('max_steps', 10) + 2

        if len(self._agent_messages) > max_steps:
            output_response = OutputResponse(
                response_content_type='text/markdown',
                response_status=200,
                response_body='Exceeded max steps. Terminating.',
                response_headers={},
            )
            bookkeeping_data = BookKeepingData(
                run_data={**output_response._asdict()}, input=self._input, config={}, output={'agent_messages': self._agent_messages}, timestamp=time.time(),
            )
            self._output_stream.bookkeep(bookkeeping_data)

            async_to_sync(self._output_stream.write_raw)(
                Message(
                    message_type=MessageType.AGENT_DONE,
                    message_from='agent',
                )
            )
            return

        if message.message_type == MessageType.BEGIN and message.message_to == self._id:
            logger.info(f'Agent actor {self.actor_urn} started')

            model = self._config.get('model', 'gpt-3.5-turbo')

            if model == 'gpt-3.5-turbo-latest':
                model = 'gpt-3.5-turbo-1106'
            elif model == 'gpt-4-turbo-latest':
                model = 'gpt-4-1106-preview'

            # Make one call to the model
            full_content = ''
            function_name = ''
            function_args = ''
            finish_reason = None
            result = self._openai_client.chat.completions.create(
                model=model,
                messages=self._agent_messages,
                stream=True,
                functions=self._functions,
            )
            agent_message_id = str(uuid.uuid4())

            for data in result:
                logger.info(data)
                if data.object == 'chat.completion.chunk' and len(data.choices) > 0 and data.choices[0].delta:
                    finish_reason = data.choices[0].finish_reason
                    delta = data.choices[0].delta
                    function_call = delta.function_call
                    content = delta.content

                    if function_call and function_call.name:
                        function_name += function_call.name
                        async_to_sync(self._output_stream.write)(
                            AgentOutput(
                                content=FunctionCall(
                                    name=function_call.name,
                                ),
                                id=agent_message_id,
                                from_id='agent',
                                type='step',
                            )
                        )
                    elif function_call and function_call.arguments:
                        function_args += function_call.arguments
                        async_to_sync(self._output_stream.write)(
                            AgentOutput(
                                content=FunctionCall(
                                    arguments=function_call.arguments,
                                ),
                                id=agent_message_id,
                                from_id='agent',
                                type='step',
                            )
                        )
                    elif content:
                        full_content += content
                        async_to_sync(self._output_stream.write)(
                            AgentOutput(
                                content=content,
                                id=agent_message_id,
                                from_id='agent',
                                type='output',
                            )
                        )

            if function_name and finish_reason == 'function_call':
                logger.info(
                    f'Agent function call: {function_name}({function_args})')

                self._agent_messages.append({
                    'role': 'assistant',
                    'content': None,
                    'function_call': {
                        'name': function_name,
                        'arguments': function_args
                    },
                })

                try:
                    tool_invoke_input = ToolInvokeInput(
                        tool_name=function_name,
                        tool_args=json.loads(function_args),
                    )
                    async_to_sync(self._output_stream.write_raw)(
                        Message(
                            message_id=agent_message_id,
                            message_type=MessageType.TOOL_INVOKE,
                            message=tool_invoke_input,
                            message_to=function_name,
                            message_from=self._id,
                        )
                    )
                except Exception as e:
                    logger.error(f'Error invoking tool {function_name}: {e}')
                    self._on_error(Message(
                        message_from='agent',
                        message=f'Error invoking tool {function_name}: {e}',
                    ))
            elif full_content and finish_reason == 'stop':
                output_response = OutputResponse(
                    response_content_type='text/markdown',
                    response_status=200,
                    response_body=full_content,
                    response_headers={},
                )
                bookkeeping_data = BookKeepingData(
                    run_data={**output_response._asdict()}, input=self._input, config={}, output={'agent_messages': self._agent_messages}, timestamp=time.time(),
                )
                self._output_stream.bookkeep(bookkeeping_data)

                async_to_sync(self._output_stream.write_raw)(
                    Message(
                        message_type=MessageType.AGENT_DONE,
                        message_from='agent',
                    )
                )

        if message.message_type == MessageType.STREAM_DATA:
            processor_template = self._processor_configs[
                message.message_from]['processor']['output_template']

            if message.message_from in self._processor_configs:
                async_to_sync(self._output_stream.write)(
                    AgentOutput(
                        content=FunctionCall(
                            output=message.message,
                        ),
                        from_id=message.message_from,
                        id=message.response_to,
                        type='step',
                    )
                )

        if message.message_type == MessageType.STREAM_CLOSED:
            # Get the output from the processor invoke and resume the loop
            try:
                processor_template = self._processor_configs[
                    message.message_from]['processor']['output_template']

                processor_output = Template(processor_template['markdown']).render(
                    **{message.message_from: message.message})

                self._agent_messages.append({
                    'role': 'function',
                    'content': processor_output,
                    'name': message.message_from
                })

                self.actor_ref.tell(
                    Message(message_type=MessageType.BEGIN, message=None, message_to=self._id))
            except Exception as e:
                logger.error(f'Error getting tool output: {e}')

        if message.message_type == MessageType.STREAM_ERROR:
            # Log the error and quit for now
            self._on_error(message)

    def on_stop(self) -> None:
        super().on_stop()

    def get_dependencies(self):
        return list(set([x['template_key'] for x in self._processor_configs.values()]))
