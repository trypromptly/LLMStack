import asyncio
import json
import logging
from typing import Optional

from asgiref.sync import async_to_sync
from google.cloud.speech_v2 import SpeechAsyncClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.assets.stream import AssetStream
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.google import get_project_id_from_env

logger = logging.getLogger(__name__)


class SpeechToTextInput(ApiProcessorSchema):
    audio: str = Field(
        default="",
        description="Audio input either as an objref or base64 encoded string.",
    )


class SpeechToTextOutput(ApiProcessorSchema):
    text: Optional[str] = Field(
        default="",
        description="Converted text from audio input",
    )
    objref: Optional[str] = Field(
        default="",
        description="Object reference if requested",
    )


class SpeechToTextConfiguration(ApiProcessorSchema):
    objref: Optional[bool] = Field(
        default=False,
        description="Return output as object reference instead of raw text.",
        json_schema_extra={"advanced_parameter": True},
    )
    project_id: Optional[str] = Field(default=None, description="Google project ID.")
    auth_token: Optional[str] = Field(
        default=None,
        description="Authentication credentials.",
    )


class SpeechToTextProcessor(
    ApiProcessorInterface[SpeechToTextInput, SpeechToTextOutput, SpeechToTextConfiguration],
):
    # TODO: Implement non-streaming version for this processor
    @staticmethod
    def name() -> str:
        return "Speech To Text"

    @staticmethod
    def slug() -> str:
        return "speech_to_text"

    @staticmethod
    def description() -> str:
        return "Convert speech to text"

    @staticmethod
    def provider_slug() -> str:
        return "google"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{text}}""",
        )

    async def _recognize_speech(self, input_asset_stream):
        client = SpeechAsyncClient.from_service_account_info(
            json.loads(self._env.get("google_service_account_json_key", "{}")),
        )

        recognition_config = cloud_speech_types.RecognitionConfig(
            auto_decoding_config=cloud_speech_types.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="latest_long",
        )
        streaming_config = cloud_speech_types.StreamingRecognitionConfig(config=recognition_config)
        config_request = cloud_speech_types.StreamingRecognizeRequest(
            recognizer=f"projects/{self._project_id}/locations/global/recognizers/_",
            streaming_config=streaming_config,
        )

        async def request_generator(config, input_asset_stream):
            yield config

            for chunk in input_asset_stream.read(timeout=5000):
                if len(chunk) == 0:
                    break

                yield cloud_speech_types.StreamingRecognizeRequest(audio=chunk)
                await asyncio.sleep(0.1)

        # Make the request
        stream = await client.streaming_recognize(requests=request_generator(config_request, input_asset_stream))

        # Handle the response
        async for response in stream:
            if response.results and response.results[0].alternatives and response.results[0].alternatives[0].transcript:
                await self._output_stream.write(SpeechToTextOutput(text=response.results[0].alternatives[0].transcript))

    def process(self) -> dict:
        self._project_id = None

        if self._config.project_id:
            self._project_id = self._config.project_id
        else:
            self._project_id = get_project_id_from_env(self._env)

        if not self._input.audio or not self._input.audio.startswith("objref://"):
            return

        asset = self._get_session_asset_instance(self._input.audio)
        if not asset:
            return

        input_asset_stream = AssetStream(asset)

        async_to_sync(self._recognize_speech)(input_asset_stream)

        output = self._output_stream.finalize()
        return output
