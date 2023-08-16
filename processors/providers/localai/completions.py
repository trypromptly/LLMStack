from typing import List
from typing import Optional
from pydantic import Field, confloat, conint
from common.blocks.http import HttpAPIProcessor, HttpMethod, JsonBody
from common.blocks.http import HttpAPIProcessorInput
from common.blocks.http import HttpAPIProcessorOutput
from processors.providers.api_processor_interface import TEXT_WIDGET_NAME, ApiProcessorInterface, ApiProcessorSchema

from asgiref.sync import async_to_sync

class CompletionsInput(ApiProcessorSchema):
    prompt: str = Field(description="Prompt text")

class CompletionsOutput(ApiProcessorSchema):
    choices: List[str] = Field(default=[], widget=TEXT_WIDGET_NAME)

class CompletionsConfiguration(ApiProcessorSchema):
    base_url: str = Field(description="Base URL", advanced_parameter=False)
    model: str = Field(description="Model name", widget='customselect', advanced_parameter=False, options=['ggml-gpt4all-j'])

    max_tokens: Optional[conint(ge=1, le=4096)] = Field(
        1024,
        description="The maximum number of [tokens](/tokenizer) to generate in the completion.\n\nThe token count of your prompt plus `max_tokens` cannot exceed the model's context length. Most models have a context length of 2048 tokens (except for the newest models, which support 4096).\n",
        example=1024,
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description='What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n',
        example=1,
        advanced_parameter=False
    )
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)] = Field(
        default=1,
        description='An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.\n\nWe generally recommend altering this or `temperature` but not both.\n',
        example=1,
    )
    timeout : Optional[int] = Field(default=60, description="Timeout in seconds", example=60)

class CompletionsProcessor(ApiProcessorInterface[CompletionsInput, CompletionsOutput, CompletionsConfiguration]):
    def name() -> str:
        return 'local ai/completions'

    def slug() -> str:
        return 'localai_completions'
    
    def process(self) -> dict:
        api_request_body = {
            "model" : self._config.model,
            "prompt": self._input.prompt,
        }
        if self._config.temperature:
            api_request_body["temperature"] = self._config.temperature
        if self._config.top_p:
            api_request_body["top_p"] = self._config.top_p
        if self._config.max_tokens:
            api_request_body["max_tokens"] = self._config.max_tokens
        
        
        http_input = HttpAPIProcessorInput(
            url=f"{self._config.base_url}/v1/completions",
            method=HttpMethod.POST,
            body=JsonBody(json_body=api_request_body)
        )
        http_api_processor = HttpAPIProcessor({'timeout': self._config.timeout})
        http_response = http_api_processor.process(
            http_input.dict(),
        )
        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            choices = list(map(lambda entry: entry['text'], http_response.content_json['choices']))            
        else:
            raise Exception("Error in processing request, details: {}".format(http_response.content))
        
        async_to_sync(self._output_stream.write)(CompletionsOutput(choices=choices))
        output = self._output_stream.finalize()
        return output
    