import logging
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from common.promptly.blocks.vendor.cohere import CohereAPIInputEnvironment
from common.promptly.blocks.vendor.cohere import CohereGenerateAPIProcessor
from common.promptly.blocks.vendor.cohere import CohereGenerateAPIProcessorConfiguration
from common.promptly.blocks.vendor.cohere import CohereGenerateAPIProcessorInput
from common.promptly.blocks.vendor.cohere import CohereGenerateAPIProcessorOutput
from common.promptly.blocks.vendor.cohere import CohereGenerateAPIProcessorOutputMetadata
from common.promptly.blocks.vendor.cohere import GenerateModel
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import BaseSchema

logger = logging.getLogger(__name__)


class GenerateInput(CohereGenerateAPIProcessorInput, BaseSchema):
    env: Optional[CohereAPIInputEnvironment] = Field(widget='hidden')


class GenerateOutput(CohereGenerateAPIProcessorOutput, BaseSchema):
    metadata: Optional[CohereGenerateAPIProcessorOutputMetadata] = Field(
        widget='hidden',
    )


class GenerateConfiguration(CohereGenerateAPIProcessorConfiguration, BaseSchema):
    model: GenerateModel = Field(
        advanced_parameter=False,
        default=GenerateModel.MEDIUM,
        description='The size of the model to generate with. Currently available models are medium and xlarge (default). Smaller models are faster, while larger models will perform better. Custom models can also be supplied with their full ID.',
    )

    preset: Optional[str] = Field(
        default=None, description='The ID of a custom playground preset. You can create presets in the playground. If you use a preset, the prompt parameter becomes optional, and any included parameters will override the preset\'s parameters.', widget='hidden',
    )


class Generate(ApiProcessorInterface[GenerateInput, GenerateOutput, GenerateConfiguration]):
    """
    Cohere Generate API
    """
    def name() -> str:
        return 'cohere_generate'

    def slug() -> str:
        return 'cohere_generate'

    def process(self) -> dict:
        _env = self._env
        api_input = GenerateInput(**self._input)

        cohere_generate_api_processor_input = CohereGenerateAPIProcessorInput(
            env=_env, prompt=api_input.prompt,
        )

        cohere_generate_api_processor = CohereGenerateAPIProcessor(
            configuration=self._config.dict(),
        )

        result = cohere_generate_api_processor.process(
            input=cohere_generate_api_processor_input.dict(),
        )

        async_to_sync(self._output_stream.write)(
            GenerateOutput(
            metadata=result.metadata, choices=result.choices,
            ),
        )
        output = self._output_stream.finalize()

        return output
