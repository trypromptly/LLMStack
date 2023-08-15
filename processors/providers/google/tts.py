import logging
from typing import Optional

import requests
from asgiref.sync import async_to_sync
from pydantic import BaseModel
from pydantic import Field

from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import AUDIO_WIDGET_NAME
from processors.providers.api_processor_interface import ApiProcessorSchema

SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


logger = logging.getLogger(__name__)


class VoiceConfig(BaseModel):
    languageCode: str = Field(
        default='en-gb', description='Language code for the voice.',
    )
    name: str = Field(
        default='en-GB-Standard-A', description='Voice name.',
    )
    ssmlGender: str = Field(
        default='FEMALE', description='Voice gender.',
    )


class AudioConfig(BaseModel):
    audioEncoding: str = Field(
        default='MP3', description='Audio encoding format.',
    )


class TextToSpeechInput(ApiProcessorSchema):
    input_text: str = Field(
        default='', description='Text to convert to speech.',
    )


class TextToSpeechOutput(ApiProcessorSchema):
    audio_content: Optional[str] = Field(
        default=None, description='The output audio content in base64 format.', widget=AUDIO_WIDGET_NAME,
    )


class TextToSpeechConfiguration(ApiProcessorSchema):
    voice: VoiceConfig = Field(
        default=VoiceConfig(), description='Voice configuration.',
    )
    audio_config: AudioConfig = Field(
        default=AudioConfig(), description='Audio configuration.',
    )
    auth_token: Optional[str] = Field(
        description='Authentication credentials.',
    )


class TextToSpeechProcessor(ApiProcessorInterface[TextToSpeechInput, TextToSpeechOutput, TextToSpeechConfiguration]):
    def name() -> str:
        return 'google_text_to_speech'

    def slug() -> str:
        return 'google_text_to_speech'

    def process(self) -> dict:
        api_url = 'https://texttospeech.googleapis.com/v1/text:synthesize'
        token = self._config.auth_token if self._config.auth_token else self._env.get(
            'google_api_key', None,
        )

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8',
        }

        data = {
            'input': {'text': input.get('input_text')},
            'voice': self._config.voice.dict(),
            'audioConfig': self._config.audio_config.dict(),
        }

        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        audio_content = f"data:audio/mp3;base64,{response_data['audioContent']}"

        async_to_sync(self._output_stream.write)(
            TextToSpeechOutput(audio_content=audio_content),
        )

        output = self._output_stream.finalize()
        return output
