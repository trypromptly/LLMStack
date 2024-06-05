import logging
from enum import Enum
from typing import List, Optional, Union

import openai
from asgiref.sync import async_to_sync
from pydantic import Field, confloat, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    TEXT_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class CompletionsModel(str, Enum):
    TEXT_DAVINCI_003 = "text-davinci-003"
    TEXT_DAVINCI_002 = "text-davinci-002"
    TEXT_CURIE_001 = "text-curie-001"
    TEXT_BABBAGE_001 = "text-babbage-001"
    TEXT_ADA_001 = "text-ada-001"
    GPT_3_5_TURBO_INSTRUCT = "gpt-3.5-turbo-instruct"

    def __str__(self):
        return self.value


class CompletionsInput(ApiProcessorSchema):
    prompt: str = Field(
        default="",
        description="The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.\n\n"
        + "Note that <|endoftext|> is the document separator that the model sees during training, so if a prompt is not specified the model will generate as if from the beginning of a new document.",
    )


class CompletionsOutput(ApiProcessorSchema):
    choices: List[str] = Field(default=[], widget=TEXT_WIDGET_NAME)
    api_response: Optional[dict] = Field(
        default={},
        description="Raw processor output.",
        widget="hidden",
    )


class CompletionsConfiguration(ApiProcessorSchema):
    model: CompletionsModel = Field(
        default=CompletionsModel.GPT_3_5_TURBO_INSTRUCT,
        description="ID of the model to use. You can use the [List models](/docs/api-reference/models/list) API to see all of your available models, or see our [Model overview](/docs/models/overview) for descriptions of them.",
        widget="customselect",
        advanced_parameter=False,
    )
    suffix: Optional[str] = Field(
        None,
        description="The suffix that comes after a completion of inserted text.",
        example="test.",
    )
    max_tokens: Optional[conint(ge=1, le=4096)] = Field(
        1024,
        description="The maximum number of [tokens](/tokenizer) to generate in the completion.\n\nThe token count of your prompt plus `max_tokens` cannot exceed the model's context length. Most models have a context length of 2048 tokens (except for the newest models, which support 4096).\n",
        example=1024,
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n",
        example=1,
    )
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)] = Field(
        default=1,
        description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. "
        + "So 0.1 means only the tokens comprising the top 10% probability mass are considered.\n\nWe generally recommend altering this or `temperature` but not both.\n",
        example=1,
    )
    n: Optional[conint(ge=1, le=128)] = Field(
        1,
        description="How many completions to generate for each prompt.\n\n**Note:** Because this parameter generates many completions, it can quickly consume your token quota. Use carefully and ensure that you have reasonable settings for `max_tokens` and `stop`.\n",
        example=1,
        hidden=True,
    )
    logprobs: Optional[conint(ge=0, le=5)] = Field(
        None,
        description="Include the log probabilities on the `logprobs` most likely tokens, as well the chosen tokens. For example, if `logprobs` is 5, "
        + "the API will return a list of the 5 most likely tokens. The API will always return the `logprob` of the sampled token, so there may be up to `logprobs+1` elements in the response.\n\nThe maximum value for `logprobs` is 5. "
        + "If you need more than this, please contact us through our [Help center](https://help.openai.com) and describe your use case.\n",
    )
    echo: Optional[bool] = Field(
        False,
        description="Echo back the prompt in addition to the completion\n",
    )
    stop: Optional[Union[str, List[str]]] = Field(
        None,
        description="Up to 4 sequences where the API will stop generating further tokens. The returned text will not contain the stop sequence.\n",
    )
    presence_penalty: Optional[confloat(ge=-2.0, le=2.0)] = Field(
        0,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, "
        + "increasing the model's likelihood to talk about new topics.\n\n[See more information about frequency and presence penalties.](/docs/api-reference/parameter-details)\n",
    )
    frequency_penalty: Optional[confloat(ge=-2.0, le=2.0)] = Field(
        0,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, "
        + "decreasing the model's likelihood to repeat the same line verbatim.\n\n[See more information about frequency and presence penalties.](/docs/api-reference/parameter-details)\n",
    )


class Completions(
    ApiProcessorInterface[CompletionsInput, CompletionsOutput, CompletionsConfiguration],
):
    """
    OpenAI Completions
    """

    @staticmethod
    def name() -> str:
        return "Completions"

    @staticmethod
    def slug() -> str:
        return "completions"

    @staticmethod
    def description() -> str:
        return "Generates completions for the given prompt"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""{% for choice in choices %}
{{choice}}
{% endfor %}""",
        )

    def process(self) -> dict:
        client = openai.OpenAI(api_key=self._env["openai_api_key"])
        result = client.completions.create(
            stream=True,
            model=self._config.model,
            prompt=self._input.prompt,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
            n=1,
        )

        for data in result:
            async_to_sync(self._output_stream.write)(
                CompletionsOutput(
                    choices=list(map(lambda x: x.text, data.choices)),
                ),
            )

        output = self._output_stream.finalize()
        return output
