import logging
from typing import Literal

from asgiref.sync import async_to_sync
from openai import OpenAI
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class TextToSpeechModel(StrEnum):
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"


class TextToSpeechVoice(StrEnum):
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class TextToSpeechInput(ApiProcessorSchema):
    input_text: str = Field(
        default="",
        description="Text to convert to speech.",
    )


class TextToSpeechConfiguration(ApiProcessorSchema):
    model: TextToSpeechModel = Field(
        default=TextToSpeechModel.TTS_1,
        description="OpenAI model to use.",
        json_schema_extra={"advanced_parameter": False},
    )
    voice: TextToSpeechVoice = Field(
        default=TextToSpeechVoice.ALLOY,
        description="Voice to use.",
        json_schema_extra={"advanced_parameter": False},
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
            markdown="""<pa-asset url="{{result}}" controls type="audio/mpeg"></pa-media>""",
        )

    def process(self) -> dict:
        output_stream = self._output_stream
        provider_config = self.get_provider_config(
            model_slug=self._config.model,
        )
        openai_client = OpenAI(api_key=provider_config.api_key)

        output = None

        with openai_client.with_streaming_response.audio.speech.create(
            input=self._input.input_text,
            model=self._config.model,
            voice=self._config.voice,
            response_format=self._config.response_format,
            speed=self._config.speed,
        ) as response:
            asset_stream = self._create_asset_stream(mime_type=f"audio/{self._config.response_format}")
            async_to_sync(
                output_stream.write,
            )(
                TextToSpeechOutput(
                    result=asset_stream.objref,
                ),
            )

            for audio_bytes in response.iter_bytes():
                if asset_stream and audio_bytes:
                    asset_stream.append_chunk(audio_bytes)

            if asset_stream:
                asset_stream.finalize()

            output = self._output_stream.finalize()
        return output
