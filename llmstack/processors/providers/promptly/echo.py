import logging

from asgiref.sync import async_to_sync

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class EchoProcessorInput(ApiProcessorSchema):
    input_str: str = 'Hello World!'
    stream: bool = False


class EchoProcessorOutput(ApiProcessorSchema):
    output_str: str = ''


class EchoProcessorConfiguration(ApiProcessorSchema):
    pass


class EchoProcessor(ApiProcessorInterface[EchoProcessorInput, EchoProcessorOutput, EchoProcessorConfiguration]):
    """
    Echo processor
    """

    @staticmethod
    def name() -> str:
        return 'Echo'

    @staticmethod
    def slug() -> str:
        return 'echo'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> dict:
        output_stream = self._output_stream
        if self._input.stream:
            for chunk in self._input.input_str.split(' '):
                async_to_sync(output_stream.write)(
                    EchoProcessorOutput(output_str=f'{chunk} '),
                )
        else:
            async_to_sync(output_stream.write)(
                EchoProcessorOutput(output_str=self._input.input_str),
            )

        output = output_stream.finalize()
        return output
