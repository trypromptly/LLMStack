import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Union

from asgiref.sync import async_to_sync
from pydantic import confloat
from pydantic import conint
from pydantic import Field

from common.blocks.llm.openai import CompletionsModel
from common.blocks.llm.openai import OpenAICompletionsAPIProcessor
from common.blocks.llm.openai import OpenAICompletionsAPIProcessorConfiguration
from common.blocks.llm.openai import OpenAICompletionsAPIProcessorInput
from common.blocks.llm.openai import OpenAICompletionsAPIProcessorOutput
from common.utils.utils import get_key_or_raise
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import ApiProcessorSchema
from processors.providers.api_processor_interface import TEXT_WIDGET_NAME


logger = logging.getLogger(__name__)


class CompletionsInput(ApiProcessorSchema):
    prompt: str = Field(default='', description='The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.\n\nNote that <|endoftext|> is the document separator that the model sees during training, so if a prompt is not specified the model will generate as if from the beginning of a new document.')


class CompletionsOutput(ApiProcessorSchema):
    choices: List[str] = Field(default=[], widget=TEXT_WIDGET_NAME)
    api_response: Optional[dict] = Field(
        default={}, description='Raw processor output.', widget='hidden',
    )


class CompletionsConfiguration(OpenAICompletionsAPIProcessorConfiguration, ApiProcessorSchema):
    model: CompletionsModel = Field(
        default=CompletionsModel.TEXT_DAVINCI_003,
        description='ID of the model to use. You can use the [List models](/docs/api-reference/models/list) API to see all of your available models, or see our [Model overview](/docs/models/overview) for descriptions of them.',
        widget='customselect',
        advanced_parameter=False,
    )
    max_tokens: Optional[conint(ge=1, le=4096)] = Field(
        1024,
        description="The maximum number of [tokens](/tokenizer) to generate in the completion.\n\nThe token count of your prompt plus `max_tokens` cannot exceed the model's context length. Most models have a context length of 2048 tokens (except for the newest models, which support 4096).\n",
        example=1024,
        advanced_parameter=False,
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description='What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n',
        example=1,
        advanced_parameter=False,
    )
    n: Optional[conint(ge=1, le=128)] = Field(
        1,
        description='How many completions to generate for each prompt.\n\n**Note:** Because this parameter generates many completions, it can quickly consume your token quota. Use carefully and ensure that you have reasonable settings for `max_tokens` and `stop`.\n',
        example=1,
        widget='hidden',
    )
    stream: Optional[bool] = Field(
        widget='hidden', advanced_parameter=True, default=True,
    )
    logit_bias: Optional[Dict[str, Any]] = Field(
        default={}, widget='hidden', advanced_paramete=True,
    )


class Completions(ApiProcessorInterface[CompletionsInput, CompletionsOutput, CompletionsConfiguration]):
    """
    OpenAI Completions
    """
    def name() -> str:
        return 'open ai/completions'

    def slug() -> str:
        return 'openai_completions'

    def process(self) -> dict:
        _env = self._env

        completions_api_processor_input = OpenAICompletionsAPIProcessorInput(
            env=_env, prompt=get_key_or_raise(self._input.dict(), 'prompt', 'No prompt found in input'),
        )
        if self._config.stream != True:
            raise Exception('Stream must be true for this processor.')

        result_iter: Generator[OpenAICompletionsAPIProcessorOutput, None, None] = OpenAICompletionsAPIProcessor(
            configuration=self._config.dict(),
        ).process_iter(completions_api_processor_input.dict())

        for result in result_iter:
            async_to_sync(self._output_stream.write)(
                CompletionsOutput(choices=result.choices, api_response=result.metadata.raw_response),
            )

        output = self._output_stream.finalize()
        return output
