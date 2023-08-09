import base64
import logging
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from common.promptly.blocks.vendor.openai import OpenAIAPIInputEnvironment
from common.promptly.blocks.vendor.openai import OpenAIAPIProcessorOutputMetadata
from common.promptly.blocks.vendor.openai import OpenAIAudioTranslationsProcessor
from common.promptly.blocks.vendor.openai import OpenAIAudioTranslationsProcessorConfiguration
from common.promptly.blocks.vendor.openai import OpenAIAudioTranslationsProcessorInput
from common.promptly.blocks.vendor.openai import OpenAIAudioTranslationsProcessorOutput
from common.promptly.blocks.vendor.openai import OpenAIFile
from common.promptly.core.base import BaseErrorOutput
from common.utils.utils import get_key_or_raise
from common.utils.utils import validate_parse_data_uri
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import BaseSchema
from processors.providers.api_processor_interface import DataUrl


logger = logging.getLogger(__name__)


class AudioTranslationsInput(BaseSchema):
    file: str = Field(
        default='',
        description='The audio file to transcribe, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.', accepts={'audio/*': []},  maxSize=20000000, widget='file',
    )
    file_data: Optional[str] = Field(
        default='', description='The base64 encoded data of audio file to transcribe', pattern=r'data:(.*);name=(.*);base64,(.*)',
    )
    prompt: Optional[str] = Field(
        default=None, description='An optional text to guide the model\'s style or continue a previous audio segment. The prompt should match the audio language.',
    )


class AudioTranslationsOutput(OpenAIAudioTranslationsProcessorOutput, BaseSchema):
    text: str = Field(
        default='', description='The translated text', widget='textarea',
    )
    metadata: Optional[OpenAIAPIProcessorOutputMetadata] = Field(
        default=None, description='Metadata about the API call', widget='hidden',
    )


class AudioTranslationsConfiguration(OpenAIAudioTranslationsProcessorConfiguration, BaseSchema):
    model: str = Field(
        default='whisper-1',
        description='ID of the model to use. Only `whisper-1` is currently available.\n',
        advanced_parameter=False,
    )


class AudioTranslations(ApiProcessorInterface[AudioTranslationsInput, AudioTranslationsOutput, AudioTranslationsConfiguration]):

    """
    OpenAI Audio Translations API
    """
    def name() -> str:
        return 'open ai/audio_translations'

    def slug() -> str:
        return 'openai_audio_translations'

    def process(self) -> dict:
        _env = self._env
        input = self._input.dict()

        if 'file' in input and len(input['file']) > 0:
            mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
                self._input.file,
            )
        elif 'file_data' in input and len(input['file_data']) > 0:
            mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
                self._input.file_data,
            )
        else:
            raise Exception('No file or file_data found in input')

        file_data = base64.b64decode(base64_encoded_data)
        audio_translation_api_processor_input = OpenAIAudioTranslationsProcessorInput(
            env=OpenAIAPIInputEnvironment(
                openai_api_key=get_key_or_raise(
                _env, 'openai_api_key', 'No openai_api_key found in _env',
                ),
            ),
            prompt=self._input.prompt, file=OpenAIFile(
                name=file_name, content=file_data, mime_type=mime_type,
            ),
        )
        response: OpenAIAudioTranslationsProcessorOutput = OpenAIAudioTranslationsProcessor(
            configuration=self._config.dict(),
        ).process(
                input=audio_translation_api_processor_input.dict(),
        )
        async_to_sync(self._output_stream.write)(
            AudioTranslationsOutput(text=response.text),
        )

        output = self._output_stream.finalize()

        return output
