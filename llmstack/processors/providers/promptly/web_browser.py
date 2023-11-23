import base64
import logging
from enum import Enum
from time import sleep
from typing import List, Optional

import grpc
import openai
import orjson as json
from asgiref.sync import async_to_sync
from django.conf import settings
from google.protobuf.json_format import MessageToJson
from pydantic import BaseModel, Field, validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class Model(str, Enum):
    GPT_3_5_LATEST = 'gpt-3.5-turbo-latest'
    GPT_3_5 = 'gpt-3.5-turbo'
    GPT_3_5_16K = 'gpt-3.5-turbo-16k'
    GPT_4 = 'gpt-4'
    GPT_4_32K = 'gpt-4-32k'
    GPT_4_LATEST = 'gpt-4-turbo-latest'

    def __str__(self):
        return self.value


class WebBrowserConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        description='Connection to use', widget='connection', advanced_parameter=False)
    model: Model = Field(
        description='Backing model to use', default=Model.GPT_4_LATEST, advanced_parameter=False)
    stream_video: bool = Field(
        description='Stream video of the browser', default=False)
    stream_text: bool = Field(
        description='Stream output text from the browser', default=False)
    timeout: int = Field(
        description='Timeout in seconds', default=10, ge=1, le=100)
    max_steps: int = Field(
        description='Maximum number of browsing steps', default=10, ge=1, le=20)
    system_message: str = Field(
        description='System message to use', default='You are a helpful assistant that browses internet using a web browser tool and accomplishes user provided task.')


class BrowserInstructionType(str, Enum):
    CLICK = 'Click'
    TYPE = 'Type'
    WAIT = 'Wait'
    GOTO = 'Goto'
    COPY = 'Copy'
    SCROLL_X = 'ScrollX'
    SCROLL_Y = 'ScrollY'

    def __str__(self):
        return self.value


class BrowserInstruction(BaseModel):
    type: BrowserInstructionType
    selector: Optional[str] = None
    data: Optional[str] = None

    @validator('type', pre=True, always=True)
    def validate_type(cls, v):
        return v.lower().capitalize()


class WebBrowserOutput(ApiProcessorSchema):
    text: str = Field(default='', description='Text of the result')
    video: Optional[str] = Field(
        default=None, description='Video of the result')


class WebBrowserInput(ApiProcessorSchema):
    start_url: str = Field(
        description='URL to visit to start the session')
    task: str = Field(
        ..., description='Details of the task to perform')


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_browser_instructions",
            "description": "Run a series of browser instructions as specified by an array of step objects. Returns the page content after all instructions have been executed. Page content contains text, buttons, input fields and link details that can be used to inform the next instruction.",
            "parameters": {
                "type": "object",
                "description": "An object containing an array of browser instruction steps to be executed.",
                "properties": {
                    "steps": {
                        "type": "array",
                        "title": "Browser Instruction Steps",
                        "description": "An ordered list of instructions for the browser to execute. Each step is an object containing instruction details.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["Click", "Type", "Wait", "Goto", "Copy", "ScrollX", "ScrollY"],
                                    "title": "Instruction Type",
                                    "description": "The type of action to perform in the browser (e.g., 'Click' a button, 'Type' into a field, 'ScrollX' by 500 in pixels)."
                                },
                                "selector": {
                                    "type": "string",
                                    "title": "Element Selector",
                                    "description": "The CSS selector used to identify the target element for the action."
                                },
                                "data": {
                                    "type": "string",
                                    "title": "Instruction Data",
                                    "description": "Additional data needed for the instruction, such as text to type, the URL to navigate to, time in seconds to wait, ScrollX in pixels etc ."
                                }
                            },
                            "required": ["type"],
                            "title": "Step",
                            "description": "A single step containing the type, selector, and data needed to perform a browser action."
                        },
                        "title": "Steps",
                        "description": "The series of steps to be performed in the browser session."
                    }
                },
                "required": ["steps"]
            }
        }
    }
]


class WebBrowser(ApiProcessorInterface[WebBrowserInput, WebBrowserOutput, WebBrowserConfiguration]):
    """
    Browse a given URL
    """
    @staticmethod
    def name() -> str:
        return 'Web Browser'

    @staticmethod
    def slug() -> str:
        return 'web_browser'

    @staticmethod
    def description() -> str:
        return 'Browse web based on instructions'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(markdown='')

    def _request_iterator(self, start_url) -> Optional[runner_pb2.PlaywrightBrowserRequest]:
        # Our first instruction is always to goto the start_url
        playwright_start_request = runner_pb2.PlaywrightBrowserRequest()
        playwright_start_request.url = start_url
        playwright_start_request.timeout = self._config.timeout if self._config.timeout and self._config.timeout > 0 and self._config.timeout <= 100 else 100
        playwright_start_request.session_data = self._env['connections'][self._config.connection_id][
            'configuration']['_storage_state'] if self._config.connection_id else ''
        playwright_start_request.stream_video = self._config.stream_video

        yield playwright_start_request

        while not self._terminated:
            if self._instructions_processed_index >= len(self._instructions):
                sleep(0.1)
                continue

            playwright_request = runner_pb2.PlaywrightBrowserRequest()
            instructions = self._instructions[self._instructions_processed_index]
            for step in instructions['steps']:
                if step.type == BrowserInstructionType.GOTO:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.GOTO, data=step.data)
                if step.type == BrowserInstructionType.CLICK:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.CLICK, selector=step.selector)
                elif step.type == BrowserInstructionType.WAIT:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.WAIT, selector=step.selector)
                elif step.type == BrowserInstructionType.COPY:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.COPY, selector=step.selector)
                elif step.type == BrowserInstructionType.TYPE:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.TYPE, selector=step.selector, data=step.data)
                elif step.type == BrowserInstructionType.SCROLL_X:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.SCROLL_X, selector=step.selector, data=step.data)
                elif step.type == BrowserInstructionType.SCROLL_Y:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.SCROLL_Y, selector=step.selector, data=step.data)
                playwright_request.steps.append(input)
            playwright_request.url = start_url
            playwright_request.timeout = self._config.timeout if self._config.timeout and self._config.timeout > 0 and self._config.timeout <= 100 else 100
            playwright_request.session_data = self._env['connections'][self._config.connection_id][
                'configuration']['_storage_state'] if self._config.connection_id else ''
            playwright_request.stream_video = self._config.stream_video

            self._instructions_processed_index += 1

            yield playwright_request

        terminate_request = runner_pb2.PlaywrightBrowserRequest()
        terminate_request.steps.append(runner_pb2.BrowserInput(
            type=runner_pb2.TERMINATE))
        yield terminate_request

    def process(self) -> dict:
        self._instructions = []
        self._instructions_processed_index = 0

        model = self._config.model if self._config.model else Model.GPT_3_5_LATEST
        if model == 'gpt-3.5-turbo-latest':
            model = 'gpt-3.5-turbo-1106'
        elif model == 'gpt-4-turbo-latest':
            model = 'gpt-4-1106-preview'

        messages = [{
            'role': 'system',
            'content': self._config.system_message
        }, {
            'role': 'user',
            'content': self._input.task
        }]

        self._terminated = False
        self._instructions = []
        output_stream = self._output_stream
        output_text = ''
        channel = grpc.insecure_channel(
            f'{settings.RUNNER_HOST}:{settings.RUNNER_PORT}')
        stub = runner_pb2_grpc.RunnerStub(channel)

        playwright_response_iter = stub.GetPlaywrightBrowser(
            self._request_iterator(self._input.start_url))

        # Wait till we get the first playwright non video response
        for response in playwright_response_iter:
            if response.content.text:
                browser_response = MessageToJson(response)
                tool_call_message = {
                    'role': 'assistant',
                    'tool_calls': [
                            {
                                'id': 'initial_message',
                                'function': {
                                    'name': 'run_browser_instructions',
                                    'arguments': '{\n  "steps": []\n}',
                                },
                                'type': 'function',
                            }
                    ],
                }
                tool_message = {
                    'role': 'tool',
                    'tool_call_id': 'initial_message',
                    'name': 'run_browser_instructions',
                    'content': browser_response,
                }
                messages.append(tool_call_message)
                messages.append(tool_message)
                break
            elif response.video:
                # Send base64 encoded video
                async_to_sync(output_stream.write)(WebBrowserOutput(
                    text='',
                    video=f"data:videostream;name=browser;base64,{base64.b64encode(response.video).decode('utf-8')}"
                ))

        if response.state == runner_pb2.TERMINATED:
            output_text = "".join([x.text for x in response.outputs])
            if not output_text:
                output_text = response.content.text
            self._terminated = True

        openai_client = openai.OpenAI(api_key=self._env['openai_api_key'])
        total_steps = 1
        while not self._terminated:
            if total_steps > self._config.max_steps:
                self._terminated = True
                break

            total_steps += 1

            # Check tool responses and trim old messages
            if len(messages) > 4:
                for message in messages[:-2]:
                    if message['role'] == 'tool':
                        message['content'] = ''

            result = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                tools=TOOLS,
            )
            function_calls = []
            content = ''
            finish_reason = None
            tool_call_id = None
            for data in result:
                choice = data.choices[0] if len(
                    data.choices) > 0 else None
                if not choice or not choice.delta:
                    continue

                content += choice.delta.content if choice.delta.content else ''
                tool_call_chunks = choice.delta.tool_calls if choice.delta.tool_calls else []
                finish_reason = choice.finish_reason
                for tool_call_chunk in tool_call_chunks:
                    function_name = tool_call_chunk.function.name if tool_call_chunk.function and tool_call_chunk.function.name and tool_call_chunk.type == 'function' else ''
                    function_arguments = tool_call_chunk.function.arguments if tool_call_chunk.function and tool_call_chunk.function.arguments else ''

                    if tool_call_chunk.index < len(function_calls):
                        function_calls[tool_call_chunk.index].update({
                            'name': function_calls[tool_call_chunk.index]['name'] + function_name,
                            'arguments': function_calls[tool_call_chunk.index]['arguments'] + function_arguments,
                        })
                    else:
                        if tool_call_chunk.type == 'function':
                            tool_call_id = tool_call_chunk.id

                        function_calls.append({
                            'name': function_name,
                            'arguments': function_arguments,
                        })

                # Stream text content to the output
                if choice.delta.content and self._config.stream_text:
                    async_to_sync(output_stream.write)(WebBrowserOutput(
                        text=choice.delta.content
                    ))

            if finish_reason == 'tool_calls':
                # Convert function arguments to dict
                for function_call in function_calls:
                    function_call['arguments_json'] = function_call['arguments']
                    try:
                        function_call['arguments'] = json.loads(
                            function_call['arguments'])
                    except:
                        pass
            elif finish_reason == 'stop':
                output_text += content
                self._terminated = True
                break

            # Iterate through function calls and convert to browser instructions
            for function_call in function_calls:
                if function_call['name'] == 'run_browser_instructions':
                    steps = []
                    for step in function_call['arguments']['steps']:
                        try:
                            steps.append(BrowserInstruction(
                                type=step['type'],
                                selector=step['selector'] if 'selector' in step else None,
                                data=step['data'] if 'data' in step else None,
                            ))
                        except Exception as e:
                            logger.exception(e)
                            self._terminated = True
                            break

                    self._instructions.append({'steps': steps})

            try:
                # Get the next response from the browser and generate the next set of instructions
                for response in playwright_response_iter:
                    if response.video:
                        # Send base64 encoded video
                        async_to_sync(output_stream.write)(WebBrowserOutput(
                            text='',
                            video=f"data:videostream;name=browser;base64,{base64.b64encode(response.video).decode('utf-8')}"
                        ))
                    elif response.content.text:
                        # Pass the page content as response to tool_call
                        browser_response = MessageToJson(response)
                        tool_call_message = {
                            'role': 'assistant',
                            'tool_calls': [
                                    {
                                        'id': tool_call_id,
                                        'function': {
                                            'name': function_call['name'],
                                            'arguments': function_call['arguments_json'],
                                        },
                                        'type': 'function',
                                    } for function_call in function_calls
                            ],
                        }
                        tool_message = {
                            'role': 'tool',
                            'tool_call_id': tool_call_id,
                            'name': 'run_browser_instructions',
                            'content': browser_response,
                        }
                        messages.append(tool_call_message)
                        messages.append(tool_message)
                        # Break to call llm again
                        break
                    else:
                        self._terminated = True
                        break

                    if response.state == runner_pb2.TERMINATED:
                        output_text = "".join(
                            [x.text for x in response.outputs])
                        if not output_text:
                            output_text = response.content.text
                        self._terminated = True
                        break

            except Exception as e:
                self._terminated = True
                logger.exception(e)
                break

        self._terminated = True
        async_to_sync(output_stream.write)(WebBrowserOutput(
            text=output_text
        ))
        output = output_stream.finalize()

        channel.close()

        return output
