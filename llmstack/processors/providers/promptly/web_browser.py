import base64
import logging
from enum import Enum
from time import sleep
from typing import Optional

import grpc
import openai
import orjson as json
from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic import BaseModel, Field, validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_MESSAGE = '''You are a helpful assistant that browses internet using a web browser tool and accomplishes user provided task. 
You can click on buttons, type into input fields, select options from dropdowns, copy text from elements, scroll the page and navigate to other pages. 
You can also use the text from the page to generate the next set of instructions. For example, you can use the text from a button to click on it. 
You can also use the text from a link to navigate to the URL specified in the link. Please follow the instructions below to accomplish the task.

- ONLY return a valid JSON object (no other text is necessary). Use doublequotes for property names and values. For example, use {"output": "Hello World"} instead of {'output': 'Hello World'}. Thinking of the output as a JSON object will help you generate the output in the correct format.
- Following is the JSON format for the output
{
    'output': <output>
    'instructions': [{
        'type': <type_of_instruction>,
        'tag': <tag_to_use>,
        'data': <data_to_use>
    }]
}
where <output> is your response to the user and 'instructions' is an array of instructions to browse the page

<type_of_instruction> can be one of the following:
    'Click': Click on the element identified by the tag
    'Type': Type the data into the element identified by the tag
    'Wait': Wait for the element identified by the tag to appear
    'Goto': Navigate to the URL specified in data
    'Copy': Copy the text from the element identified by the tag
    'Enter': Press the Enter key
    'Scrollx': Scroll the page horizontally by the number of pixels specified in data
    'Scrolly': Scroll the page vertically by the number of pixels specified in data
    'Terminate': Terminate the browser session if no more instructions are needed
<tag_to_use> is the identifier to use to identify the element to perform the instruction on. Identifiers are next to the elements on the page. For example all text areas have identifier with prefix `ta=`. Similar `in=`, `b=`, `a=`, `s=` are used for input fields, buttons, links and selects respectively.
<data_to_use> is the data to use for the instruction. For example, if type_of_instruction is 'Type', then data_to_use is the text to type into the element identified by tag_to_use. If type_of_instruction is 'ScrollX' or 'ScrollY', then data_to_use is the number of pixels to scroll the page by.
- If the task is done and no more instructions are needed, you can terminate the browser session by generating an instruction with type_of_instruction as 'Terminate'.
- Let's think step by step.
'''


class Model(str, Enum):
    GPT_3_5_LATEST = 'gpt-3.5-turbo-latest'
    GPT_3_5 = 'gpt-3.5-turbo'
    GPT_3_5_16K = 'gpt-3.5-turbo-16k'
    GPT_4 = 'gpt-4'
    GPT_4_32K = 'gpt-4-32k'
    GPT_4_LATEST = 'gpt-4-turbo-latest'
    GPT_4_V_LATEST = 'gpt-4-vision-latest'

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
        description='System message to use', default=DEFAULT_SYSTEM_MESSAGE, widget='textarea')


class BrowserInstructionType(str, Enum):
    CLICK = 'Click'
    TYPE = 'Type'
    WAIT = 'Wait'
    GOTO = 'Goto'
    COPY = 'Copy'
    TERMINATE = 'Terminate'
    ENTER = 'Enter'
    SCROLLX = 'Scrollx'
    SCROLLY = 'Scrolly'

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
                                    "enum": ["Click", "Type", "Wait", "Goto", "Copy", "Scrollx", "Scrolly"],
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
        return OutputTemplate(
            markdown='''![video](data:videostream/output._video)

{{text}}
''')

    def _process_browser_content(self, browser_response):
        content = browser_response.content
        output = ''

        if content.error:
            output += f'Error encountered running previous instructions: {content.error}\n\n'

        if content.text:
            output += f'Text from page:\n------\n{content.text[:10000]}\n'

        if content.buttons:
            output += f'\nButtons on page:\n------\n'
            for button in content.buttons:
                output += f'selector: {button.selector}, text: {button.text}\n'

        if content.links:
            output += f'\nLinks on page:\n------\n'
            for link in content.links[:100]:
                output += f'selector: {link.selector}, url: {link.url}, text: {link.text}\n'

        if content.inputs:
            output += f'\nInput fields on page:\n------\n'
            for input_field in content.inputs:
                output += f'selector: {input_field.selector}, text: {input_field.text}\n'

        if content.textareas:
            output += f'\nTextareas on page:\n------\n'
            for textarea in content.textareas:
                output += f'selector: {textarea.selector}, text: {textarea.text}\n'

        if content.selects:
            output += f'\nSelects on page:\n------\n'
            for select in content.selects:
                output += f'selector: {select.selector}, text: {select.text}\n'

        return output

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
                elif step.type == BrowserInstructionType.SCROLLX:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.SCROLL_X, selector=step.selector, data=step.data)
                elif step.type == BrowserInstructionType.SCROLLY:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.SCROLL_Y, selector=step.selector, data=step.data)
                elif step.type == BrowserInstructionType.TERMINATE:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.TERMINATE)
                elif step.type == BrowserInstructionType.ENTER:
                    input = runner_pb2.BrowserInput(
                        type=runner_pb2.ENTER)
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
        elif model == 'gpt-4-vision-latest':
            model = 'gpt-4-vision-preview'

        messages = [{
            'role': 'system',
            'content': self._config.system_message,
        }, {
            'role': 'user',
            'content': f'Perform the following task: {self._input.task}'
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
            if response.content.text or response.content.screenshot:
                browser_text_response = self._process_browser_content(response)
                browser_response = browser_text_response
                if self._config.model == Model.GPT_4_V_LATEST:
                    browser_response = [{
                        'type': 'text',
                        'text': browser_text_response,
                    }]
                    if response.content.screenshot:
                        browser_response.append({
                            'type': 'image_url',
                            'image_url': {
                                'url': f"data:image/png;base64,{base64.b64encode(response.content.screenshot).decode('utf-8')}",
                            },
                        })
                messages.append({
                    'role': 'user',
                    'content': browser_response,
                })
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
                logger.info(
                    f'Max steps reached: {total_steps} and {self._config.max_steps}')
                self._terminated = True
                break

            total_steps += 1

            # Check tool responses and trim old messages
            if len(messages) > 3:
                for message in messages[:-3]:
                    if message['role'] == 'user':
                        if type(message['content']) == list:
                            for content in message['content']:
                                if content['type'] == 'image_url':
                                    message['content'].remove(content)
                                elif content['type'] == 'text':
                                    content['text'] = content['text'][:300]
                        else:
                            message['content'] = message['content'][:300]

            chat_completions_args = {
                'model': model,
                'messages': messages,
                'max_tokens': 4000,
            }

            if self._config.model is not Model.GPT_4_V_LATEST:
                chat_completions_args['response_format'] = {
                    "type": "json_object"}

            result = openai_client.chat.completions.create(
                **chat_completions_args,
            )

            if result.object == 'chat.completion':
                # Clean up messages
                try:
                    content = result.choices[0].message.content
                    if content.startswith('```json'):
                        content = content.replace('```json', '')

                    if content.startswith('```'):
                        content = content.replace('```', '')

                    if content.startswith('json'):
                        content = content.replace('json', '')

                    if content.endswith('```'):
                        content = content.replace('```', '')

                    try:
                        result = json.loads(content)
                    except:
                        result = {
                            'output': content,
                        }

                    if 'instructions' in result:
                        steps = []
                        for instruction in result['instructions']:
                            instruction_type = instruction['type']
                            steps.append(BrowserInstruction(
                                type=instruction_type,
                                selector=instruction['selector'] if 'selector' in instruction else instruction[
                                    'tag'] if 'tag' in instruction else None,
                                data=instruction['data'] if 'data' in instruction else None,
                            ))

                        self._instructions.append({'steps': steps})
                    else:
                        self._instructions.append({'steps': [BrowserInstruction(
                            type='Wait',
                            data='1',
                        )]})

                    messages.append({
                        'role': 'assistant',
                        'content': result['output'] if 'output' in result else '',
                    })

                    if 'output' in result and self._config.stream_text:
                        async_to_sync(output_stream.write)(
                            WebBrowserOutput(text=result['output'] + '\n\n'))
                    elif 'output' in result:
                        output_text += result['output'] + '\n\n'
                except Exception as e:
                    logger.exception(e)
                    self._terminated = True
                    break

            try:
                # Get the next response from the browser and generate the next set of instructions
                for response in playwright_response_iter:
                    if response.video:
                        # Send base64 encoded video
                        async_to_sync(output_stream.write)(WebBrowserOutput(
                            text='',
                            video=f"data:videostream;name=browser;base64,{base64.b64encode(response.video).decode('utf-8')}"
                        ))
                    elif response.content.text or response.content.screenshot:
                        browser_text_response = self._process_browser_content(
                            response)
                        browser_response = browser_text_response
                        if self._config.model == Model.GPT_4_V_LATEST:
                            browser_response = [{
                                'type': 'text',
                                'text': browser_text_response,
                            }]
                            if response.content.screenshot:
                                browser_response.append({
                                    'type': 'image_url',
                                    'image_url': {
                                        'url': f"data:image/png;base64,{base64.b64encode(response.content.screenshot).decode('utf-8')}",
                                    },
                                })
                        messages.append({
                            'role': 'user',
                            'content': browser_response,
                        })
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
