import base64
import logging
from enum import Enum
from typing import Literal

from asgiref.sync import async_to_sync
from openai import OpenAI
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class TextToSpeechModel(str, Enum):
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"

    def __str__(self) -> str:
        return self.value


class TextToSpeechVoice(str, Enum):
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

    def __str__(self) -> str:
        return self.value


class TextToSpeechInput(ApiProcessorSchema):
    input_text: str = Field(
        default="",
        description="Text to convert to speech.",
    )


class TextToSpeechConfiguration(ApiProcessorSchema):
    model: TextToSpeechModel = Field(
        default=TextToSpeechModel.TTS_1,
        description="OpenAI model to use.",
        advanced_parameter=False,
    )
    voice: TextToSpeechVoice = Field(
        default=TextToSpeechVoice.ALLOY,
        description="Voice to use.",
        advanced_parameter=False,
    )
    response_format: Literal["mp3", "opus", "aac", "flac"] = Field(
        default="mp3",
        description="Format of the response audio.",
    )
    speed: float = Field(
        ge=0.0,
        le=4.0,
        default=1.0,
        description="Speed of the voice.",
    )


class TextToSpeechOutput(ApiProcessorSchema):
    result: str = Field(
        default=None,
        description="The output audio content in base64 format.",
    )


class TextToSpeechProcessor(
    ApiProcessorInterface[TextToSpeechInput, TextToSpeechOutput, TextToSpeechConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Text to Speech"

    @staticmethod
    def slug() -> str:
        return "text_to_speech"

    @staticmethod
    def description() -> str:
        return "Convert text to speech"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""![Audio]({{result}})""",
        )

    def process(self) -> dict:
        output_stream = self._output_stream
        openai_client = OpenAI(api_key=self._env["openai_api_key"])

        response = openai_client.audio.speech.create(
            input=self._input.input_text,
            model=self._config.model,
            voice=self._config.voice,
            response_format=self._config.response_format,
            speed=self._config.speed,
        )

        for audio_bytes in response.iter_bytes():
            base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            data_uri = f"data:audio/{self._config.response_format};name=sample.{self._config.response_format};base64,{base64_audio}"
            async_to_sync(
                output_stream.write,
            )(
                TextToSpeechOutput(
                    result=data_uri,
                ),
            )

        output = self._output_stream.finalize()
        return output
