import json
import logging 
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, confloat, conint
from processors.providers.api_processor_interface import CHAT_WIDGET_NAME, ApiProcessorInterface, ApiProcessorSchema
from common.blocks.http import BearerTokenAuth, HttpAPIProcessor, HttpMethod, JsonBody, NoAuth
from common.blocks.http import HttpAPIProcessorInput
from common.blocks.http import HttpAPIProcessorOutput

from asgiref.sync import async_to_sync


logger = logging.getLogger(__name__)

class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    FUNCTION = 'function'

    def __str__(self):
        return self.value
    
class FunctionCallResponse(BaseModel):
    name: Optional[str]
    arguments: Optional[str]
    
class ChatMessage(BaseModel):
    role: Optional[Role] = Field(
        default=Role.USER, description="The role of the message sender. Can be 'user' or 'assistant' or 'system'.",
    )
    content: Optional[str] = Field(
        default='', description='The message text.', widget='textarea',
    )
    name: Optional[str] = Field(
        default='', widget='hidden',
        description='The name of the author of this message or the function name.',
    )
    function_call: Optional[FunctionCallResponse] = Field(
        widget='hidden',
        description='The name and arguments of a function that should be called, as generated by the model.',
    )

class ChatCompletionInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default='', description='A message from the system, which will be prepended to the chat history.', widget='textarea',
    )
    messages: List[ChatMessage] = Field(
        default=[ChatMessage()], description='A list of messages, each with a role and message text.',
    )

class ChatCompletionsOutput(ApiProcessorSchema):
    choices: List[ChatMessage] = Field(
        default=[], description='Messages', widget=CHAT_WIDGET_NAME,
    )
    _api_response: Optional[dict] = Field(
        default={}, description='Raw processor output.',
    )

class ChatCompletionsConfiguration(ApiProcessorSchema):
    base_url: Optional[str] = Field(description="Base URL")
    model: str = Field(description="Model name", widget='customselect', advanced_parameter=False, 
                       options=['ggml-gpt4all-j'], default='ggml-gpt4all-j')
    max_tokens: Optional[conint(ge=1, le=32000)] = Field(
        1024,
        description='The maximum number of tokens allowed for the generated answer. By default, the number of tokens the model can return will be (4096 - prompt tokens).\n',
        example=1024,
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description='What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n',
        example=1,
        advanced_parameter=False,
    )
    timeout: int = Field(default=60, description='Timeout in seconds')

class ChatCompletions(ApiProcessorInterface[ChatCompletionInput, ChatCompletionsOutput, ChatCompletionsConfiguration]):
    def name() -> str:
        return 'local ai/chatgpt'

    def slug() -> str:
        return 'localai_chatcompletions'
    
    def process(self) -> dict:
        env = self._env
        base_url = env.get("localai_base_url") 
        if self._config.base_url:
            base_url = self._config.base_url
            
        if not base_url:
            raise Exception("Base URL is not set")
            
        system_message = self._input.system_message
        
        chat_messages = [{"role": "system", "content": system_message}] if system_message else []
        for msg_entry in self._input.messages:
            chat_messages.append(json.loads( msg_entry.json()))
                        
        
        api_request_body = {
            "model": self._config.model,
            "messages" : chat_messages,
            "temperature": self._config.temperature,
        }
        http_input = HttpAPIProcessorInput(
            url=f"{base_url}/v1/chat/completions",
            authorization= BearerTokenAuth(token=env.get("localai_api_key")) if env.get("localai_api_key") else NoAuth(),

            method=HttpMethod.POST,
            body=JsonBody(json_body=api_request_body)
        )
        http_api_processor = HttpAPIProcessor({'timeout': self._config.timeout})
        http_response = http_api_processor.process(
            http_input.dict(),
        )
        
        logger.info("ChatCompletions response: {}".format(http_response.content_json))
        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            choices = list(map(lambda x: ChatMessage(**x['message']), http_response.content_json['choices']))       
        else:
            raise Exception("Error in processing request, details: {}".format(http_response.content))
        
        async_to_sync(self._output_stream.write)(ChatCompletionsOutput(choices=choices))
        output = self._output_stream.finalize()
        return output