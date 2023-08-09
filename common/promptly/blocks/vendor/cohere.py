import json
import logging
from enum import Enum
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional

from pydantic import Field

from common.promptly.blocks.http import APIKeyAuth
from common.promptly.blocks.http import HttpAPIError
from common.promptly.blocks.http import HttpAPIProcessor
from common.promptly.blocks.http import HttpAPIProcessorInput
from common.promptly.blocks.http import HttpAPIProcessorOutput
from common.promptly.blocks.http import JsonBody
from common.promptly.core.base import BaseConfiguration
from common.promptly.core.base import BaseConfigurationType
from common.promptly.core.base import BaseErrorOutput
from common.promptly.core.base import BaseInput
from common.promptly.core.base import BaseInputEnvironment
from common.promptly.core.base import BaseInputType
from common.promptly.core.base import BaseOutput
from common.promptly.core.base import BaseOutputType
from common.promptly.core.base import BaseProcessor
from common.promptly.core.base import Schema

logger = logging.getLogger(__name__)


def process_cohere_error_response(response: HttpAPIProcessorOutput) -> str:
    """
        Processes the error response from Cohere API
    """
    return response.text


class GenerateModel(str, Enum):
    MEDIUM = 'medium'
    XLARGE = 'xlarge'

    def __str__(self):
        return self.value


class CohereAPIInputEnvironment(BaseInputEnvironment):
    cohere_api_key: str = Field(..., description='Cohere API Key')
    user: Optional[str] = Field(default='', description='User')


class CohereGenerateAPIProcessorInput(BaseInput):
    prompt: str = Field(defult='', description='The prompt to generate from.')
    env: Optional[CohereAPIInputEnvironment]


class CohereGenerateAPIProcessorOutputMetadata(Schema):
    is_cached: bool = Field(
        False, description='Whether the response was served from cache',
    )
    raw_response: dict = Field(
        {}, description='The raw response from the API',
    )


class CohereGenerateAPIProcessorOutput(BaseOutput):
    choices: List[str] = Field(
        [], description='The list of generated completions.',
    )
    metadata: Optional[CohereGenerateAPIProcessorOutputMetadata]


class CohereGenerateAPIProcessorConfiguration(BaseConfiguration):
    model: GenerateModel = Field(
        default=GenerateModel.MEDIUM, description='The size of the model to generate with. Currently available models are medium and xlarge (default). Smaller models are faster, while larger models will perform better. Custom models can also be supplied with their full ID.',
    )

    num_generations: Optional[int] = Field(
        default=1, description='Defaults to 1, min value of 1, max value of 5. Denotes the maximum number of generations that will be returned.',
    )

    max_tokens: Optional[int] = Field(
        default=20, description='Denotes the number of tokens to predict per generation, defaults to 20. See BPE Tokens for more details. Can only be set to 0 if return_likelihoods is set to ALL to get the likelihood of the prompt',
    )

    preset: Optional[str] = Field(
        default=None, description='The ID of a custom playground preset. You can create presets in the playground. If you use a preset, the prompt parameter becomes optional, and any included parameters will override the preset\'s parameters.',
    )

    temperature: Optional[float] = Field(
        default=0.75, description='Defaults to 0.75, min value of 0.0, max value of 5.0. A non-negative float that tunes the degree of randomness in generation. Lower temperatures mean less random generations. See Temperature for more details.',
    )

    k: Optional[int] = Field(
        default=0, description='Defaults to 0(disabled), which is the minimum. Maximum value is 500. Ensures only the top k most likely tokens are considered for generation at each step.',
    )

    p: Optional[float] = Field(default=0.75, description='Defaults to 0.75. Set to 1.0 or 0 to disable. If set to a probability 0.0 < p < 1.0, it ensures that only the most likely tokens, with total probability mass of p, are considered for generation at each step. If both k and p are enabled, p acts after k.')

    frequency_penalty: Optional[float] = Field(
        default=0.0, description='Defaults to 0.0, min value of 0.0, max value of 1.0. Can be used to reduce repetitiveness of generated tokens. The higher the value, the stronger a penalty is applied to previously present tokens, proportional to how many times they have already appeared in the prompt or prior generation.',
    )

    presence_penalty: Optional[float] = Field(
        default=0.0, description='Defaults to 0.0, min value of 0.0, max value of 1.0. Can be used to reduce repetitiveness of generated tokens. Similar to frequency_penalty, except that this penalty is applied equally to all tokens that have already appeared, regardless of their exact frequencies.',
    )

    end_sequences: Optional[List[str]] = Field(
        default=None, description='The generated text will be cut at the beginning of the earliest occurence of an end sequence. The sequence will be excluded from the text.',
    )

    stop_sequences: Optional[List[str]] = Field(
        default=None, description='The generated text will be cut at the end of the earliest occurence of a stop sequence. The sequence will be included the text.',
    )

    return_likelihoods: Optional[str] = Field(
        default='NONE', description='One of GENERATION|ALL|NONE to specify how and if the token likelihoods are returned with the response. Defaults to NONE. If GENERATION is selected, the token likelihoods will only be provided for generated text. If ALL is selected, the token likelihoods will be provided both for the prompt and the generated text.',
    )

    truncate: Optional[str] = Field(default='END', description='One of NONE|START|END to specify how the API will handle inputs longer than the maximum token length. Passing START will discard the start of the input. END will discard the end of the input. In both cases, input is discarded until the remaining input is exactly the maximum input token length for the model. If NONE is selected, when the input exceeds the maximum input token length an error will be returned.')


class CohereGenerateAPIProcessor(BaseProcessor[CohereGenerateAPIProcessorInput, CohereGenerateAPIProcessorOutput, CohereGenerateAPIProcessorConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    @staticmethod
    def name() -> str:
        return 'cohere_generate_api_processor'

    def _get_api_url(self) -> str:
        return 'https://api.cohere.ai/v1/generate'

    def _get_api_headers(self, input: CohereGenerateAPIProcessorInput, configuration: CohereGenerateAPIProcessorConfiguration) -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _process(self, input: CohereGenerateAPIProcessorInput, configuration: CohereGenerateAPIProcessorConfiguration) -> CohereGenerateAPIProcessorOutput:
        http_api_processor = HttpAPIProcessor({'timeout': 5})

        http_response = http_api_processor.process(
            HttpAPIProcessorInput(
                url=self._get_api_url(),
                method='POST',
                body=JsonBody(
                    json_body=json.dumps({'prompt': input.prompt}),
                ),
                headers=self._get_api_headers(input, configuration),
                authorization=APIKeyAuth(api_key=input.env.cohere_api_key),
            ).dict(),
        )

        # If the response is ok, return the choices
        if isinstance(http_response, HttpAPIProcessorOutput) and http_response.is_ok:
            generations = json.loads(http_response.text).get('generations')
            choices = list(map(lambda x: x.get('text'), generations))

            return CohereGenerateAPIProcessorOutput(
                choices=choices,
                metadata=CohereGenerateAPIProcessorOutputMetadata(
                    raw_response={
                        'api_response': json.loads(http_response.text),
                    },
                ),
            )
        else:
            raise Exception(process_cohere_error_response(http_response))
