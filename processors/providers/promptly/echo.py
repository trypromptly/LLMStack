import logging

from asgiref.sync import async_to_sync

from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import BaseSchema

logger = logging.getLogger(__name__)


class EchoProcessorInput(BaseSchema):
    input_str: str = 'Hello World!'
    stream: bool = False


class EchoProcessorOutput(BaseSchema):
    output_str: str = ''


class EchoProcessorConfiguration(BaseSchema):
    pass


class EchoProcessor(ApiProcessorInterface[EchoProcessorInput, EchoProcessorOutput, EchoProcessorConfiguration]):
    """
    Echo processor
    """

    def name() -> str:
        return 'promptly/echo'

    def slug() -> str:
        return 'promptly_echo'

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
