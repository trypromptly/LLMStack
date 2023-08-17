import json
import logging
from typing import List, Optional

from pydantic import confloat, conint
from common.blocks.http import HttpAPIProcessorOutput
from common.blocks.llm.openai import OpenAIAPIProcessor, OpenAIAPIProcessorConfiguration, OpenAIAPIProcessorInput, OpenAIAPIProcessorOutput

logger = logging.getLogger(__name__)

class LocalAICompletionsAPIProcessorInput(OpenAIAPIProcessorInput):
    prompt: str

class LocalAICompletionsAPIProcessorOutput(OpenAIAPIProcessorOutput):
    choices: List[str]
    
class LocalAICompletionsAPIProcessorConfiguration(OpenAIAPIProcessorConfiguration):
    base_url: Optional[str] 
    model: str

    max_tokens: Optional[conint(ge=1, le=4096)] 
    
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)]
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)]
    stream: Optional[bool] 
    
    timeout : Optional[int]
    
class LocalAICompletionsAPIProcessor(OpenAIAPIProcessor[LocalAICompletionsAPIProcessorInput, LocalAICompletionsAPIProcessorOutput, LocalAICompletionsAPIProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'localai_completions_api_processor'

    def _get_api_url(self) -> dict:
        return '{}/completions'.format(self.configuration.base_url)

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(self, input: LocalAICompletionsAPIProcessorInput, configuration: LocalAICompletionsAPIProcessorConfiguration) -> dict:
        return {
            'model': configuration.model,
            'prompt': input.prompt,
            'max_tokens': configuration.max_tokens,
            'temperature': configuration.temperature,
            'top_p': configuration.top_p,
            'stream': configuration.stream,
        }

    def _transform_streaming_api_response(self, input: LocalAICompletionsAPIProcessorInput, configuration: LocalAICompletionsAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> LocalAICompletionsAPIProcessorOutput:
        text = response.content.decode('utf-8')
        json_response = json.loads(text.split('data: ')[1])
        choices = list(
            map(lambda x: x.get('text', ''), json_response['choices']),
        )
        return LocalAICompletionsAPIProcessorOutput(choices=choices, metadata=json_response)

    def _transform_api_response(self, input: LocalAICompletionsAPIProcessorInput, configuration: LocalAICompletionsAPIProcessorConfiguration, response: HttpAPIProcessorOutput) -> LocalAICompletionsAPIProcessorOutput:
        choices = list(
            map(lambda x: x.get('text', ''), json.loads(response.text)['choices']),
        )
        json_response = json.loads(response.text)
        
        return LocalAICompletionsAPIProcessorOutput(choices=choices, metadata=json_response)