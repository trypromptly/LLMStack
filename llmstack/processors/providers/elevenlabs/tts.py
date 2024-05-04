import logging
from typing import Optional

import requests
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    AUDIO_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


# A utility function to sanitize input string as it may contain markdown
# characters
def sanitize_input(input):
    return input.replace("*", "").replace("_", "").replace("`", "")


class VoiceSettings(BaseModel):
    similarity_boost: float = Field(
        default=0.75,
        description="Boosting voice clarity and target speaker similarity is achieved by high enhancement; however, very high values can produce artifacts, so it's essential to find the optimal setting.",
    )
    stability: float = Field(
        default=0.75,
        description="Higher stability ensures consistency but may result in monotony, therefore for longer text, it is recommended to decrease stability.",
    )


class TextToSpeechInput(ApiProcessorSchema):
    input_text: str = Field(
        default="",
        description="Text to convert to speech.",
    )


class TextToSpeechOutput(ApiProcessorSchema):
    audio_content: Optional[str] = Field(
        default=None,
        description="The output audio content in base64 format.",
        widget=AUDIO_WIDGET_NAME,
    )


class TextToSpeechConfiguration(ApiProcessorSchema):
    voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="Voice ID to be used, you can use https://api.elevenlabs.io/v1/voices to list all the available voices.",
        advanced_parameter=False,
    )
    model_id: str = Field(
        default="eleven_monolingual_v1",
        description="Identifier of the model that will be used, you can query them using GET https://api.elevenlabs.io/v1/models.",
        advanced_parameter=False,
    )
    optimize_streaming_latency: int = Field(
        default=0,
        description="You can turn on latency optimizations at some cost of quality. The best possible final latency varies by model. "
        + "Possible values: 0 - default mode (no latency optimizations) 1 - normal latency optimizations, 2 - strong latency optimizations, "
        + "3 - max latency optimizations, 4 - max latency optimizations, but also with text normalizer turned off for even more latency savings (best latency, but can mispronounce eg numbers and dates).",
        maximum=4,
        minimum=0,
    )
    voice_settings: VoiceSettings = Field(
        default=VoiceSettings(),
        description="Voice settings.",
    )


class ElevenLabsTextToSpeechProcessor(
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
        return "Transforms text into speech in a given voice"

    @staticmethod
    def provider_slug() -> str:
        return "elevenlabs"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown="""<pa-asset url="{{audio_content}}" controls type="audio/mpeg"></pa-media>""",
        )

    def process(self) -> dict:
        api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._config.voice_id}/stream"

        headers = {
            "accept": "audio/mpeg",
            "xi-api-key": self._env.get("elevenlabs_api_key", None),
            "Content-Type": "application/json",
        }

        data = {
            "text": sanitize_input(self._input.input_text),
            "model_id": self._config.model_id,
            "voice_settings": self._config.voice_settings.dict(),
        }

        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            stream=True,
        )
        response.raise_for_status()

        asset_stream = self._create_asset_stream(mime_type="audio/mpeg")
        async_to_sync(self._output_stream.write)(
            TextToSpeechOutput(audio_content=asset_stream.objref),
        )

        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                if asset_stream and chunk:
                    asset_stream.append_chunk(chunk)

        if asset_stream:
            asset_stream.finalize()

        output = self._output_stream.finalize()
        return output
