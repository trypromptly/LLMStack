import json
import logging
from enum import Enum
from typing import Generator, Generic, List, Optional

from pydantic import Field

from llmstack.common.blocks.base.processor import (BaseConfiguration,
                                                   BaseConfigurationType,
                                                   BaseInput,
                                                   BaseInputEnvironment,
                                                   BaseInputType, BaseOutput,
                                                   BaseOutputType, Schema)
from llmstack.common.blocks.http import (BearerTokenAuth, HttpAPIProcessor,
                                         HttpAPIProcessorInput,
                                         HttpAPIProcessorOutput, JsonBody)
from llmstack.common.blocks.llm import LLMBaseProcessor

DEFAULT_TIMEOUT = 120

logger = logging.getLogger(__name__)


def process_azure_openai_error_response(
    response: HttpAPIProcessorOutput,
) -> str:
    """
    Processes the error response from OpenAI
    """
    if response.content_json:
        if "error" in response.content_json:
            if "message" in response.content_json["error"]:
                return response.content_json["error"]["message"]
            return response.content_json["error"]
        elif "message" in response.content_json:
            return response.content_json["message"]
        else:
            return response.text
    else:
        return response.text


class AzureOpenAIAPIInputEnvironment(BaseInputEnvironment):
    azure_openai_api_key: str = Field(..., description="Azure OpenAI API Key")
    user: Optional[str] = Field(default="", description="User")


class AzureOpenAIAPIProcessorOutputMetadata(Schema):
    raw_response: dict = Field(
        {},
        description="The raw response from the API",
    )
    is_cached: bool = Field(
        False,
        description="Whether the response was served from cache",
    )


class AzureOpenAIAPIProcessorInput(BaseInput):
    env: Optional[AzureOpenAIAPIInputEnvironment] = Field(
        ...,
        description="Environment variables",
    )


class AzureOpenAIAPIProcessorConfiguration(BaseConfiguration):
    base_url: str = Field(
        description="This value can be found in the Keys & Endpoint section when examining your resource from the Azure portal. An example endpoint is: https://docs-test-001.openai.azure.com/.",
    )
    deployment_name: str = Field(
        description="This value will correspond to the custom name you chose for your deployment when you deployed a model. This value can be found under Resource Management > Deployments in the Azure portal or alternatively under Management > Deployments in Azure OpenAI Studio.",
    )
    api_version: Optional[str] = Field(
        description="The API version to use",
        default="2023-03-15-preview",
    )


class AzureOpenAIAPIProcessorOutput(BaseOutput):
    metadata: Optional[AzureOpenAIAPIProcessorOutputMetadata]


class AzureOpenAIAPIProcessor(
    LLMBaseProcessor[
        AzureOpenAIAPIProcessorInput,
        AzureOpenAIAPIProcessorOutput,
        AzureOpenAIAPIProcessorConfiguration,
    ],
    Generic[
        BaseInputType,
        BaseOutputType,
        BaseConfigurationType,
    ],
):
    @property
    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
    ) -> dict:
        raise NotImplementedError()

    def _get_api_url(self) -> dict:
        raise NotImplementedError()

    def _transform_api_response(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
        response: HttpAPIProcessorOutput,
    ) -> BaseOutputType:
        raise NotImplementedError()

    def _process_iter(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
    ) -> Generator[HttpAPIProcessorOutput, None, None]:
        """
        Invokes the API processor on the input and returns output iterator
        """
        http_api_processor = HttpAPIProcessor({"timeout": DEFAULT_TIMEOUT})
        http_input = HttpAPIProcessorInput(
            url=self._get_api_url(),
            method="POST",
            body=JsonBody(
                json_body=(
                    self._get_api_request_payload(
                        input,
                        configuration,
                    )
                ),
            ),
            headers={"api-key": f"{input.env.azure_openai_api_key}"},
            authorization=BearerTokenAuth(
                token=input.env.azure_openai_api_key,
            ),
        )

        http_status_is_ok = True
        error_message = ""
        for http_response in http_api_processor.process_iter(
            http_input.dict(),
        ):
            if http_response.is_ok:
                if http_response.text == "data: [DONE]":
                    return
                else:
                    response = self._transform_streaming_api_response(
                        input,
                        configuration,
                        http_response,
                    )
                    yield response
            else:
                http_status_is_ok = False
                error_message += http_response.text

        if not http_status_is_ok:
            raise Exception(
                process_azure_openai_error_response(
                    http_response.copy(
                        update={"content_json": json.loads(error_message)},
                    ),
                ),
            )

    def _process(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
    ) -> BaseOutputType:
        """
        Invokes the API processor on the input and returns the output
        """
        http_api_processor = HttpAPIProcessor({"timeout": DEFAULT_TIMEOUT})
        http_input = HttpAPIProcessorInput(
            url=self._get_api_url(),
            method="POST",
            body=JsonBody(
                json_body=(
                    self._get_api_request_payload(
                        input,
                        configuration,
                    )
                ),
            ),
            headers={"api-key": f"{input.env.azure_openai_api_key}"},
            authorization=BearerTokenAuth(
                token=input.env.azure_openai_api_key,
            ),
        )

        http_response = http_api_processor.process(
            http_input.dict(),
        )

        # If the response is ok, return the choices
        if (
            isinstance(
                http_response,
                HttpAPIProcessorOutput,
            )
            and http_response.is_ok
        ):
            response = self._transform_api_response(
                input,
                configuration,
                http_response,
            )
            return response
        else:
            raise Exception(process_azure_openai_error_response(http_response))


class AzureOpenAICompletionsAPIProcessorInput(AzureOpenAIAPIProcessorInput):
    prompt: str = Field(
        default="",
        description="The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.\n\nNote that <|endoftext|> is the document separator that the model sees during training, so if a prompt is not specified the model will generate as if from the beginning of a new document.",
    )


class AzureOpenAICompletionsAPIProcessorOutput(AzureOpenAIAPIProcessorOutput):
    choices: List[str] = Field(
        default=[],
        description="The list of generated completions.",
    )


class AzureOpenAICompletionsAPIProcessorConfiguration(
    AzureOpenAIAPIProcessorConfiguration,
):
    pass


"""
    OpenAICompletionsAPIProcessor processor class for OpenAI Completions API
"""


class OpenAICompletionsAPIProcessor(
    AzureOpenAIAPIProcessor[
        AzureOpenAICompletionsAPIProcessorInput,
        AzureOpenAICompletionsAPIProcessorOutput,
        AzureOpenAICompletionsAPIProcessorConfiguration,
    ],
):
    @staticmethod
    def name() -> str:
        return "azure_openai_completions_api_processor"

    def _get_api_url(self) -> dict:
        return f"{self.configuration.base_url}/openai/deployments/{self.configuration.deployment_name}/completions"

    def api_url(self) -> str:
        return self._get_api_url()

    def _get_api_request_payload(
        self,
        input: AzureOpenAICompletionsAPIProcessorInput,
        configuration: AzureOpenAICompletionsAPIProcessorConfiguration,
    ) -> dict:
        return {
            "prompt": input.prompt,
        }

    def _transform_api_response(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
        response: HttpAPIProcessorOutput,
    ) -> AzureOpenAICompletionsAPIProcessorOutput:
        choices = list(
            map(lambda x: x["text"], json.loads(response.text)["choices"]),
        )
        return AzureOpenAICompletionsAPIProcessorOutput(
            choices=choices,
            metadata=AzureOpenAIAPIProcessorOutputMetadata(
                raw_response=json.loads(response.text),
            ),
        )


class Role(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"

    def __str__(self):
        return self.value


class ChatMessage(Schema):
    role: Optional[Role] = Field(
        description="The role of the author of this message.",
    )

    content: Optional[str] = Field(description="The contents of the message")


class AzureOpenAIChatCompletionsAPIProcessorInput(
    AzureOpenAIAPIProcessorInput,
):
    system_message: Optional[str] = Field(
        ...,
        description="The intial system message to be set.",
    )
    chat_history: List[ChatMessage] = Field(
        default=[],
        description="The chat history, in the [chat format](/docs/guides/chat/introduction).",
    )
    messages: List[ChatMessage] = Field(
        default=[],
        description="The messages to be sent to the API.",
    )


class AzureOpenAIChatCompletionsAPIProcessorOutput(
    AzureOpenAIAPIProcessorOutput,
):
    choices: List[ChatMessage] = Field(
        ...,
        description="Chat completions, in the [chat format](/docs/guides/chat/introduction).",
    )


class AzureOpenAIChatCompletionsAPIProcessorConfiguration(
    AzureOpenAIAPIProcessorConfiguration,
):
    temperature: Optional[float] = Field(
        le=2.0,
        ge=0.0,
        default=0.7,
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.",
    )
    top_p: Optional[float] = Field(
        description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.",
        default=1.0,
        ge=0.0,
        le=1.0,
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream back partial progress.",
    )
    max_tokens: Optional[int] = Field(
        description="The maximum number of tokens to generate.",
        ge=1,
        default=1024,
        le=32000,
    )


class AzureOpenAIChatCompletionsAPIProcessor(
    AzureOpenAIAPIProcessor[
        AzureOpenAIChatCompletionsAPIProcessorInput,
        AzureOpenAIChatCompletionsAPIProcessorOutput,
        AzureOpenAIChatCompletionsAPIProcessorConfiguration,
    ],
):
    def _get_api_url(self) -> str:
        return f"{self.configuration.base_url}/openai/deployments/{self.configuration.deployment_name}/chat/completions?api-version={self.configuration.api_version}"

    def api_url(self) -> str:
        return self._get_api_url()

    @staticmethod
    def name() -> str:
        return "azure_openai_chat_completions_api_processor"

    def _get_api_request_payload(
        self,
        input: AzureOpenAIChatCompletionsAPIProcessorInput,
        configuration: AzureOpenAIChatCompletionsAPIProcessorConfiguration,
    ) -> dict:
        input_json = json.loads(
            input.copy(
                exclude={"env"},
            ).json(),
        )
        configuration_json = json.loads(
            configuration.json(
                exclude={"base_url", "deployment_name", "api_version"},
            ),
        )

        messages = []
        if input.system_message:
            messages.append(
                {"role": "system", "content": input.system_message},
            )

        if input.chat_history and len(input.chat_history) > 0:
            messages += input_json["chat_history"]

        messages += input_json["messages"]

        return {
            **configuration_json,
            "messages": messages,
        }

    def _transform_api_response(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
        response: HttpAPIProcessorOutput,
    ) -> AzureOpenAIChatCompletionsAPIProcessorOutput:
        choices = list(
            map(
                lambda x: ChatMessage(**x["message"]),
                json.loads(response.text)["choices"],
            ),
        )

        return AzureOpenAIChatCompletionsAPIProcessorOutput(
            choices=choices,
            metadata=AzureOpenAIAPIProcessorOutputMetadata(
                raw_response=json.loads(response.text),
            ),
        )

    def _transform_streaming_api_response(
        self,
        input: AzureOpenAIAPIProcessorInput,
        configuration: AzureOpenAIAPIProcessorConfiguration,
        response: HttpAPIProcessorOutput,
    ) -> AzureOpenAIChatCompletionsAPIProcessorOutput:
        text = response.content.decode("utf-8")
        json_response = json.loads(text.split("data: ")[1])

        choices = list(
            map(lambda x: ChatMessage(**x["delta"]), json_response["choices"]),
        )

        return AzureOpenAIChatCompletionsAPIProcessorOutput(
            choices=choices,
        )
