import base64
import logging
from typing import Optional

import openai

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class AudioTranscriptionInput(ApiProcessorSchema):
    file: str = Field(
        default='', description='The audio file to transcribe, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.', accepts={'audio/*': []}, maxSize=20000000, widget='file',
    )
    file_data: Optional[str] = Field(
        default='', description='The base64 encoded data of audio file to transcribe', pattern=r'data:(.*);name=(.*);base64,(.*)',
    )
    prompt: Optional[str] = Field(
        default=None, description='An optional text to guide the model\'s style or continue a previous audio segment. The prompt should match the audio language.',
    )
    language: Optional[str] = Field(
        default=None, description='The language of the audio file. Currently, only English is supported.',
    )

class AudioTranscriptionOutput(ApiProcessorSchema):
    text: str = Field(
        default='', description='The transcribed text', widget='textarea',
    )


class AudioTranscriptionConfiguration(ApiProcessorSchema):
    model: str = Field(
        default='whisper-1',
        description='ID of the model to use. Only `whisper-1` is currently available.\n',
        advanced_parameter=False,
    )
    response_format: Optional[str] = Field(
        'json',
        description='The format of the transcript output, in one of these options: json, text, srt, verbose_json, or vtt.\n',
    )
    temperature: Optional[float] = Field(
        0,
        description='The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log_probability) to automatically increase the temperature until certain thresholds are hit.\n',
    )


class AudioTranscription(ApiProcessorInterface[AudioTranscriptionInput, AudioTranscriptionOutput, AudioTranscriptionConfiguration]):

    """
    OpenAI Audio Transcription API
    """
    @staticmethod
    def name() -> str:
        return 'Audio Transcription'

    @staticmethod
    def slug() -> str:
        return 'audio_transcriptions'

    @staticmethod
    def description() -> str:
        return 'Transcribes the given audio file into text'

    @staticmethod
    def provider_slug() -> str:
        return 'openai'

    def process(self) -> dict:        
        if self._input.file and len(self._input.file) > 0:
            mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
                self._input.file,
            )
        elif self._input.file_data and len(self._input.file_data) > 0:
            mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
                self._input.file_data,
            )
        else:
            raise Exception('No file or file_data found in input')

        file_data = base64.b64decode(base64_encoded_data)
        client = openai.OpenAI(api_key=self._env['openai_api_key'])

        transcript = client.audio.transcriptions.create(
            file=(file_name, file_data),
            model=self._config.model,
            prompt=self._input.prompt,
            language=self._input.language,
        )
        async_to_sync(self._output_stream.write)(
            AudioTranscriptionOutput(text=transcript.text),
        )

        output = self._output_stream.finalize()
        return output
