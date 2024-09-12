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


class AudioTranslationsInput(ApiProcessorSchema):
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


class AudioTranslationsOutput(ApiProcessorSchema):
    text: str = Field(
        default="",
        description="The translated text",
        json_schema_extra={"widget": "textarea"},
    )


class AudioTranslationsConfiguration(ApiProcessorSchema):
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
        description="The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. "
        + "If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log_probability) to automatically increase the temperature until certain thresholds are hit.\n",
    )


class AudioTranslations(
    ApiProcessorInterface[AudioTranslationsInput, AudioTranslationsOutput, AudioTranslationsConfiguration],
):
    """
    OpenAI Audio Translations API
    """

    @staticmethod
    def name() -> str:
        return "Audio Translation"

    @staticmethod
    def slug() -> str:
        return "audio_translations"

    @staticmethod
    def description() -> str:
        return "Transcribes and translates the given audio file based on the prompt"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
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
                self._input.file,
            )
        else:
            raise Exception("No file or file_data found in input")

        file_data = base64.b64decode(base64_encoded_data)
        provider_config = self.get_provider_config(model_slug=self._config.model)
        client = openai.OpenAI(api_key=provider_config.api_key)

        translation = client.audio.translations.create(
            file=(file_name, file_data),
            model=self._config.model,
            prompt=self._input.prompt,
            response_format=self._config.response_format,
            temperature=self._config.temperature,
        )

        async_to_sync(self._output_stream.write)(
            AudioTranslationsOutput(text=translation.text),
        )

        output = self._output_stream.finalize()

        return output
