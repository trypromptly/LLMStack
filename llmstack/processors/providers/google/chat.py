from enum import Enum
from typing import Annotated, Dict, List, Literal, Optional, Union
from asgiref.sync import async_to_sync
import google.generativeai as genai
from pydantic import BaseModel, Field
import requests
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema
from llmstack.processors.providers.google import API_KEY, get_google_credential_from_env

class GeminiModel(str, Enum):
    GEMINI_PRO = 'gemini-pro'
    GEMINI_PRO_VISION = 'gemini-pro-vision'
    
    def __str__(self):
        return self.value
    
class TextMessage(BaseModel):
    type: Literal["text"]

    text: str = Field(
        default='', description='The message text.')


class UrlImageMessage(BaseModel):
    type: Literal["image_url"]

    image_url: str = Field(
        default='', description='The image data URI.')
    
Message = Annotated[Union[TextMessage, UrlImageMessage], Field(discriminator='type')]

class ToolInput(BaseModel):
    name: str
    description: str
    parameters: Dict 

class FunctionCall(ApiProcessorSchema):
    name: str = Field(
        default='', description='The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.',
    )
    description: Optional[str] = Field(
        default=None, description='The description of what the function does.',
    )
    parameters: Optional[str] = Field(
        title='Parameters', widget='textarea',
        default=None, description='The parameters the functions accepts, described as a JSON Schema object. See the guide for examples, and the JSON Schema reference for documentation about the format.',
    )
class ChatInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default='', description='A message from the system, which will be prepended to the chat history.', widget='textarea',
    )
    messages: List[Message] = Field(default=[], description='The message text.')
    functions: Optional[List[FunctionCall]] = Field(
        default=None,
        description='A list of functions the model may generate JSON inputs for .',
    )

class SafetySetting(BaseModel):
    category: str
    threshold: str

class GenerationConfig(BaseModel):
    temperature: float = Field(
        le=1.0, ge=0.0,
        default=0.5, description='The temperature is used for sampling during the response generation.',
    )
    max_output_tokens: int = Field(
        le=8192, ge=1,
        default=2048, description='Maximum number of tokens that can be generated in the response. A token is approximately four characters. 100 tokens correspond to roughly 60-80 words.',
    )
    

class ChatConfiguration(ApiProcessorSchema):
    model: GeminiModel = Field(advanced_parameter=False, default=GeminiModel.GEMINI_PRO)
    safety_settings: List[SafetySetting]
    generation_config: GenerationConfig =  Field(advanced_parameter=False, default=GenerationConfig())
    
class Citation(BaseModel):
    startIndex: int
    endIndex: int
    url: str
    title: str
    license: str
    publicationDate: str
class CitationMetadata(BaseModel):
    citations: Optional[List[Citation]]
    
class SafetyAttributes(BaseModel):
    categories: Optional[List[str]]
    blocked: bool
    scores: List[float]
    
class ChatPrediction(BaseModel):
    content: str = Field(description='Generated prediction content.')
    citationMetadata: Optional[CitationMetadata] = Field(
        description='Metadata for the citations found in the response.',
    )
    safetyAttributes: Optional[SafetyAttributes] = Field(
        description='Safety attributes for the response.',
    )
class ChatOutput(ApiProcessorSchema):
    prediction: ChatPrediction 

class ChatProcessor(ApiProcessorInterface[ChatInput, ChatOutput, ChatConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Gemini'

    @staticmethod
    def slug() -> str:
        return 'chat'

    @staticmethod
    def description() -> str:
        return 'Google generative model'
    
    @staticmethod
    def provider_slug() -> str:
        return 'google'

    def get_image_bytes_mime_type(self, image_url: str):
        response = requests.get(image_url)
        if response.status_code != 200:
            raise ValueError(f'Invalid image URL: {image_url}')
        image_bytes = response.content
        mime_type = response.headers['Content-Type']
        return image_bytes, mime_type

    def process(self) -> dict:
        token, token_type = get_google_credential_from_env(self._env)
        if token_type != API_KEY:
            raise ValueError('Invalid token type. Gemini needs an API key.')
            
        genai.configure(api_key=token)
        
        messages = [] if self._input.system_message is None else [self._input.system_message]
        if self._config.model.value == GeminiModel.GEMINI_PRO:
            for message in self._input.messages:
                if message.type == 'image_url':
                    raise ValueError('Gemini Pro does not support image input.')
                elif message.type == 'text':
                    messages.append(message.text)

        elif self._config.model.value == GeminiModel.GEMINI_PRO_VISION:
            for message in self._input.messages:
                if message.type == 'image_url':
                    image_url = message.image_url
                    if image_url.startswith('data:'):
                        content, mime_type = image_url.split(',', 1)
                    elif image_url.startswith('http'):
                        content, mime_type = self.get_image_bytes_mime_type(image_url)
                    messages.append({
                        'mime_type': mime_type,
                        'data': content,
                    })
                elif message.type == 'text':
                    messages.append(message.text)
                 
        else:
            raise ValueError(f'Invalid model: {self._config.model.value}')
        
        
        model = genai.GenerativeModel(self._config.model.value)

        response = model.generate_content(
            contents=messages, stream=True)
        for chunk in response:
            async_to_sync(self._output_stream.write)(
                ChatOutput(prediction=ChatPrediction(content=chunk.text)),
            )
        
        
        output = self._output_stream.finalize()
        return output
