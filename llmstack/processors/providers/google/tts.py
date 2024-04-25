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
from llmstack.processors.providers.google import (
    API_KEY,
    get_google_credential_from_env,
    get_project_id_from_env,
)

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


logger = logging.getLogger(__name__)


class VoiceConfig(BaseModel):
    languageCode: str = Field(
        default="en-gb",
        description="Language code for the voice.",
    )
    name: str = Field(
        default="en-GB-Standard-A",
        description="Voice name.",
    )
    ssmlGender: str = Field(
        default="FEMALE",
        description="Voice gender.",
    )


class AudioConfig(BaseModel):
    audioEncoding: str = Field(
        default="MP3",
        description="Audio encoding format.",
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
    voice: VoiceConfig = Field(
        default=VoiceConfig(),
        description="Voice configuration.",
        advanced_parameter=False,
    )
    project_id: Optional[str] = Field(description="Google project ID.")
    audio_config: AudioConfig = Field(
        default=AudioConfig(),
        description="Audio configuration.",
    )
    auth_token: Optional[str] = Field(
        description="Authentication credentials.",
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
        return "google"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{audio_content}}""",
        )

    def process(self) -> dict:
        api_url = "https://texttospeech.googleapis.com/v1/text:synthesize"

        token = None
        project_id = None

        if self._config.project_id:
            project_id = self._config.project_id
        else:
            project_id = get_project_id_from_env(self._env)

        if self._config.auth_token:
            token = self._config.auth_token
            token_type = API_KEY
        else:
            token, token_type = get_google_credential_from_env(self._env)

        if token is None:
            raise Exception("No auth token provided.")

        if project_id is None:
            raise Exception("No project ID provided.")

        if token_type == API_KEY:
            headers = {
                "X-Goog-Api-Key": token,
                "Content-Type": "application/json; charset=utf-8",
            }
        else:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            }

        data = {
            "input": {"text": self._input.input_text},
            "voice": self._config.voice.dict(),
            "audioConfig": self._config.audio_config.dict(),
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
