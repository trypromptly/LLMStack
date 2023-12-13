from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

class Role(str, Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    
    def __str__(self):
        return self.value

class Part(BaseModel):
    
class ChatContent(BaseModel):
    role: Role = Field(
        default=Role.USER, description="The role of the message sender. Can be 'user' or 'assistant'.",
    )
    parts: List[Part] = Field(default=[], description='The message text.')

class ToolInput(BaseModel):
    name: str
    description: str
    parameters: Dict 
    
class ChatInput(ApiProcessorSchema):
    contents: List[ChatContent]
    tools: List[ToolInput]

class SafetySetting(BaseModel):
    category: str
    threshold: str

class GenerationConfig(BaseModel):
    temperature: float = Field(
        default=1.0, description='The temperature for sampling. Must be strictly positive.',
    )
    
    
class ChatConfiguration(ApiProcessorSchema):
    safety_settings: List[SafetySetting]
    generationConfig: GenerationConfig