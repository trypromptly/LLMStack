from typing import Any
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Union

from promptly.blocks.http import BearerTokenAuth
from promptly.blocks.http import HttpAPIProcessor
from promptly.blocks.http import HttpAPIProcessorConfiguration
from promptly.blocks.http import HttpAPIProcessorInput
from promptly.blocks.http import HttpAPIProcessorOutput
from promptly.blocks.http import HttpMethod
from promptly.blocks.http import JsonBody
from promptly.core.base import BaseConfiguration
from promptly.core.base import BaseConfigurationType
from promptly.core.base import BaseInput
from promptly.core.base import BaseInputEnvironment
from promptly.core.base import BaseInputType
from promptly.core.base import BaseOutput
from promptly.core.base import BaseOutputType
from promptly.core.base import BaseProcessor
from pydantic import Field
from pydantic import HttpUrl


class HuggingfaceEndpointProcessorInputEnvironment(BaseInputEnvironment):
    huggingfacehub_api_key: str = Field(
        ...,
        description='Huggingface Hub API Key',
    )


class HuggingfaceEndpointProcessorInput(BaseInput):
    env:  Optional[HuggingfaceEndpointProcessorInputEnvironment] = Field(
        ..., description='Environment variables',
    )

    model_args: Dict[str, Any] = Field(
        default={},
        description='Arguments to pass to the model',
    )
    inputs: Union[str, Dict] = Field(
        description='The prompt to pass into the model',
    )


class HuggingfaceEndpointProcessorOutput(BaseOutput):
    result: str = Field(description='The result of the model')


class HuggingfaceEndpointProcessorConfiguration(BaseConfiguration):
    endpoint_url: str = Field(description='The endpoint to call')


class HuggingfaceEndpointProcessor(BaseProcessor[HuggingfaceEndpointProcessorInput, HuggingfaceEndpointProcessorOutput, HuggingfaceEndpointProcessorConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    def _process(self, input: HuggingfaceEndpointProcessorInput, configuration: HuggingfaceEndpointProcessorConfiguration) -> HuggingfaceEndpointProcessorOutput:
        huggingfacehub_api_token = input.env.huggingfacehub_api_key
        model_params = input.dict().get('model_args', {})
        request_payload = {'inputs': input.inputs, 'parameters': model_params}

        http_input = HttpAPIProcessorInput(
            url=configuration.endpoint_url,
            method=HttpMethod.POST,
            authorization=BearerTokenAuth(token=huggingfacehub_api_token),
            body=JsonBody(json_body=request_payload),
        )
        http_response = HttpAPIProcessor(
            configuration=HttpAPIProcessorConfiguration(
            timeout=120,
            ).dict(),
        ).process(input=http_input.dict())

        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            return HuggingfaceEndpointProcessorOutput(result=http_response.text)
        else:
            raise Exception('Failed to get response from Huggingface Endpoint')
