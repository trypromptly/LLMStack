import base64
import logging
from typing import Optional

import openai
from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class AudioTranscriptionInput(ApiProcessorSchema):
    file: str = Field(
        default="",
        description="The audio file to transcribe, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.",
        json_schema_extra={"widget": "file", "accepts": {"audio/*": []}, "maxSize": 20000000},
    )
    file_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of audio file to transcribe",
    )
    prompt: Optional[str] = Field(
        default=None,
        description="An optional text to guide the model's style or continue a previous audio segment. The prompt should match the audio language.",
    )
    language: Optional[str] = Field(
        default=None,
        description="The language of the audio file. Currently, only English is supported.",
    )


class AudioTranscriptionOutput(ApiProcessorSchema):
    text: str = Field(
        default="",
        description="The transcribed text",
        json_schema_extra={"widget": "textarea"},
    )


class AudioTranscriptionConfiguration(ApiProcessorSchema):
    model: str = Field(
        default="whisper-1",
        description="ID of the model to use. Only `whisper-1` is currently available.\n",
        json_schema_extra={"advanced_parameter": False},
    )
    response_format: Optional[str] = Field(
        "json",
        description="The format of the transcript output, in one of these options: json, text, srt, verbose_json, or vtt.\n",
    )
    temperature: Optional[float] = Field(
        0,
        description="The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 "
        + "will make it more focused and deterministic. If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log_probability) to automatically increase the temperature until certain thresholds are hit.\n",
    )


class AudioTranscription(
    ApiProcessorInterface[AudioTranscriptionInput, AudioTranscriptionOutput, AudioTranscriptionConfiguration],
):
    """
    OpenAI Audio Transcription API
    """

    @staticmethod
    def name() -> str:
        return "Audio Transcription"

    @staticmethod
    def slug() -> str:
        return "audio_transcriptions"

    @staticmethod
    def description() -> str:
        return "Transcribes the given audio file into text"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{text}}""",
            jsonpath="$.text",
        )

    def process(self) -> dict:
        file = self._input.file or self._input.file_data

        # Extract from objref if it is one
        file = self._get_session_asset_data_uri(file)

        if file and len(file) > 0:
            mime_type, file_name, base64_encoded_data = validate_parse_data_uri(
                file,
            )
        else:
            raise Exception("No file or file_data found in input")

        file_data = base64.b64decode(base64_encoded_data)
        provider_config = self.get_provider_config(model_slug=self._config.model)
        client = openai.OpenAI(api_key=provider_config.api_key)

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
