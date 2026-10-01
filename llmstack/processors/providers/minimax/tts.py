from typing import Literal, Optional

import requests
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field, model_validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    AUDIO_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)


class VoiceSetting(BaseModel):
    voice_id: str = Field(min_length=1, description="MiniMax system or custom voice ID.")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    vol: float = Field(default=1.0, gt=0.0, le=10.0)
    pitch: int = Field(default=0, ge=-12, le=12)


class AudioSetting(BaseModel):
    format: Literal["mp3", "wav", "flac", "pcm"] = "mp3"
    sample_rate: Literal[8000, 16000, 22050, 24000, 32000, 44100] = 32000
    bitrate: Literal[32000, 64000, 128000, 256000] = 128000
    channel: Literal[1, 2] = 1


class PronunciationDict(BaseModel):
    tone: list[str] = Field(default_factory=list, description="Pronunciation rules in original/replacement format.")


class VoiceModify(BaseModel):
    pitch: Optional[int] = Field(default=None, ge=-100, le=100)
    intensity: Optional[int] = Field(default=None, ge=-100, le=100)
    timbre: Optional[int] = Field(default=None, ge=-100, le=100)
    sound_effects: Optional[Literal["spacious_echo", "auditorium_echo", "lofi_telephone", "robotic"]] = None


class TextToSpeechInput(ApiProcessorSchema):
    input_text: str = Field(min_length=1, max_length=9999, description="Text to convert to speech.")


class TextToSpeechConfiguration(ApiProcessorSchema):
    model: Literal[
        "speech-2.8-hd",
        "speech-2.8-turbo",
        "speech-2.6-hd",
        "speech-2.6-turbo",
        "speech-02-hd",
        "speech-02-turbo",
        "speech-01-hd",
        "speech-01-turbo",
    ] = Field(
        default="speech-2.8-hd",
        description="MiniMax speech model.",
        json_schema_extra={"advanced_parameter": False},
    )
    voice_setting: VoiceSetting = Field(
        description="Voice ID and speech controls.",
        json_schema_extra={"advanced_parameter": False},
    )
    audio_setting: AudioSetting = Field(default_factory=AudioSetting)
    language_boost: Optional[str] = Field(default=None, description="Language hint, or auto for automatic detection.")
    pronunciation_dict: Optional[PronunciationDict] = None
    voice_modify: Optional[VoiceModify] = None
    subtitle_enable: bool = False

    @model_validator(mode="after")
    def validate_voice_effects_format(self):
        if self.voice_modify is not None and self.audio_setting.format == "pcm":
            raise ValueError("Voice effects require mp3, wav, or flac audio.")
        return self


class TextToSpeechOutput(ApiProcessorSchema):
    audio_content: str = Field(
        description="Reference to the generated audio asset.",
        json_schema_extra={"widget": AUDIO_WIDGET_NAME},
    )
    mime_type: str = Field(description="The audio media type.")
    subtitle_url: Optional[str] = Field(default=None, description="Download URL for generated subtitles, if requested.")


class MiniMaxTextToSpeechProcessor(
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
        return "Convert text to speech with MiniMax."

    @staticmethod
    def provider_slug() -> str:
        return "minimax"

    @classmethod
    def get_output_template(cls) -> OutputTemplate:
        return OutputTemplate(
            markdown='<pa-asset url="{{audio_content}}" controls type="{{mime_type}}"></pa-asset>',
            jsonpath="$.audio_content",
        )

    def process(self) -> dict:
        provider_config = self.get_provider_config(model_slug=self._config.model)
        payload = self._config.model_dump(exclude_none=True)
        payload.update(text=self._input.input_text, stream=False, output_format="hex")
        response = requests.post(
            provider_config.speech_api_url,
            headers={"Authorization": f"Bearer {provider_config.api_key}"},
            json=payload,
            timeout=120,
            allow_redirects=False,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("MiniMax returned an invalid speech response.")
        base_resp = result.get("base_resp")
        if not isinstance(base_resp, dict) or base_resp.get("status_code") != 0:
            raise ValueError("MiniMax speech synthesis failed.")
        data = result.get("data")
        if not isinstance(data, dict) or data.get("status") != 2:
            raise ValueError("MiniMax speech synthesis did not complete.")
        audio_hex = data.get("audio")
        if not isinstance(audio_hex, str) or not audio_hex:
            raise ValueError("MiniMax returned no audio.")
        try:
            audio = bytes.fromhex(audio_hex)
        except ValueError as exc:
            raise ValueError("MiniMax returned invalid audio encoding.") from exc
        if not audio:
            raise ValueError("MiniMax returned no audio.")

        audio_format = self._config.audio_setting.format
        mime_type = {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac", "pcm": "audio/pcm"}[audio_format]
        asset_stream = self._create_asset_stream(mime_type=mime_type, file_name=f"speech.{audio_format}")
        asset_stream.append_chunk(audio)
        asset_stream.finalize()
        async_to_sync(self._output_stream.write)(
            TextToSpeechOutput(
                audio_content=asset_stream.objref,
                mime_type=mime_type,
                subtitle_url=data.get("subtitle_file"),
            )
        )
        return self._output_stream.finalize()
