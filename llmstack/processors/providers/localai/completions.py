import logging
from typing import Generator, List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field, confloat, conint

from llmstack.common.blocks.llm.localai import (
    LocalAICompletionsAPIProcessor,
    LocalAICompletionsAPIProcessorConfiguration,
    LocalAICompletionsAPIProcessorInput,
    LocalAICompletionsAPIProcessorOutput,
)
from llmstack.common.blocks.llm.openai import OpenAIAPIInputEnvironment
from llmstack.processors.providers.api_processor_interface import (
    TEXT_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class CompletionsInput(ApiProcessorSchema):
    prompt: str = Field(description="Prompt text")


class CompletionsOutput(ApiProcessorSchema):
    choices: List[str] = Field(default=[], json_schema_extra={"widget": TEXT_WIDGET_NAME})


class CompletionsConfiguration(ApiProcessorSchema):
    base_url: Optional[str] = Field(default=None, description="Base URL")
    model: str = Field(
        description="Model name",
        json_schema_extra={"advanced_parameter": False, "widget": "customselect"},
        options=["ggml-gpt4all-j"],
        default="ggml-gpt4all-j",
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
        json_schema_extra={"advanced_parameter": False},
    )
    top_p: Optional[confloat(ge=0.0, le=1.0, multiple_of=0.1)] = Field(
        default=1,
        description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.\n\n"
        + "We generally recommend altering this or `temperature` but not both.\n",
        example=1,
    )
    timeout: Optional[int] = Field(
        default=60,
        description="Timeout in seconds",
        example=60,
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Stream output",
        example=False,
    )


class CompletionsProcessor(
    ApiProcessorInterface[CompletionsInput, CompletionsOutput, CompletionsConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Completions"

    @staticmethod
    def slug() -> str:
        return "completions"

    @staticmethod
    def description() -> str:
        return "Text completions from LocalAI"

    @staticmethod
    def provider_slug() -> str:
        return "localai"

    def process(self) -> dict:
        env = self._env
        base_url = env.get("localai_base_url")
        api_key = env.get("localai_api_key")

        if self._config.base_url:
            base_url = self._config.base_url

        if not base_url:
            raise Exception("Base URL is not set")

        if self._config.stream:
            result_iter: Generator[LocalAICompletionsAPIProcessorOutput, None, None] = LocalAICompletionsAPIProcessor(
                configuration=LocalAICompletionsAPIProcessorConfiguration(
                    base_url=base_url,
                    model=self._config.model,
                    max_tokens=self._config.max_tokens,
                    temperature=self._config.temperature,
                    top_p=self._config.top_p,
                    timeout=self._config.timeout,
                    stream=True,
                ).model_dump(),
            ).process_iter(
                LocalAICompletionsAPIProcessorInput(
                    prompt=self._input.prompt,
                    env=OpenAIAPIInputEnvironment(openai_api_key=api_key),
                ).model_dump(),
            )
            for result in result_iter:
                async_to_sync(self._output_stream.write)(
                    CompletionsOutput(choices=result.choices),
                )

        else:
            result: LocalAICompletionsAPIProcessorOutput = LocalAICompletionsAPIProcessor(
                configuration=LocalAICompletionsAPIProcessorConfiguration(
                    base_url=base_url,
                    model=self._config.model,
                    max_tokens=self._config.max_tokens,
                    temperature=self._config.temperature,
                    top_p=self._config.top_p,
                    timeout=self._config.timeout,
                    stream=False,
                ).model_dump(),
            ).process(
                LocalAICompletionsAPIProcessorInput(
                    prompt=self._input.prompt,
                    env=OpenAIAPIInputEnvironment(
                        openai_api_key=api_key,
                    ),
                ).model_dump(),
            )
            choices = result.choices
            async_to_sync(self._output_stream.write)(
                CompletionsOutput(choices=choices),
            )

        output = self._output_stream.finalize()
        return output
