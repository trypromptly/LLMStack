from typing import Any, Dict, Optional, Union

from pydantic import Field

from llmstack.common.blocks.base.processor import (
    BaseConfiguration,
    BaseInput,
    BaseInputEnvironment,
    BaseOutput,
)
from llmstack.common.blocks.http import (
    BearerTokenAuth,
    HttpAPIProcessor,
    HttpAPIProcessorConfiguration,
    HttpAPIProcessorInput,
    HttpAPIProcessorOutput,
    HttpMethod,
    JsonBody,
)
from llmstack.common.blocks.llm import LLMBaseProcessor


class HuggingfaceEndpointProcessorInputEnvironment(BaseInputEnvironment):
    huggingfacehub_api_key: str = Field(
        ...,
        description="Huggingface Hub API Key",
    )


class HuggingfaceEndpointProcessorInput(BaseInput):
    env: Optional[HuggingfaceEndpointProcessorInputEnvironment] = Field(
        ...,
        description="Environment variables",
    )

    model_args: Dict[str, Any] = Field(
        default={},
        description="Arguments to pass to the model",
    )
    inputs: Union[str, Dict] = Field(
        description="The prompt to pass into the model",
    )


class HuggingfaceEndpointProcessorOutput(BaseOutput):
    result: str = Field(description="The result of the model")


class HuggingfaceEndpointProcessorConfiguration(BaseConfiguration):
    endpoint_url: str = Field(description="The endpoint to call")


class HuggingfaceEndpointProcessor(
    LLMBaseProcessor[
        HuggingfaceEndpointProcessorInput,
        HuggingfaceEndpointProcessorOutput,
        HuggingfaceEndpointProcessorConfiguration,
    ],
):
    @staticmethod
    def name() -> str:
        return "huggingface_endpoint_processor"

    def _process(
        self,
        input: HuggingfaceEndpointProcessorInput,
        configuration: HuggingfaceEndpointProcessorConfiguration,
    ) -> HuggingfaceEndpointProcessorOutput:
        huggingfacehub_api_token = input.env.huggingfacehub_api_key
        model_params = input.model_dump().get("model_args", {})
        request_payload = {"inputs": input.inputs, "parameters": model_params}

        http_input = HttpAPIProcessorInput(
            url=configuration.endpoint_url,
            method=HttpMethod.POST,
            authorization=BearerTokenAuth(token=huggingfacehub_api_token),
            body=JsonBody(json_body=request_payload),
        )
        http_response = HttpAPIProcessor(
            configuration=HttpAPIProcessorConfiguration(
                timeout=120,
            ).model_dump(),
        ).process(input=http_input.model_dump())

        if (
            isinstance(
                http_response,
                HttpAPIProcessorOutput,
            )
            and http_response.is_ok
        ):
            return HuggingfaceEndpointProcessorOutput(
                result=http_response.text,
            )
        else:
            raise Exception("Failed to get response from Huggingface Endpoint")
