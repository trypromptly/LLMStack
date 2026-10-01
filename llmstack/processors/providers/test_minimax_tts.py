import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import requests
from pydantic import ValidationError

from llmstack.common.utils.module_loader import get_all_sub_classes
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.minimax import MiniMaxProviderConfig
from llmstack.processors.providers.minimax.tts import (
    MiniMaxTextToSpeechProcessor,
    TextToSpeechConfiguration,
    TextToSpeechInput,
)
from llmstack.processors.providers.processors import ProcessorFactory
from llmstack.server.settings import PROVIDERS

EXPECTED_MODELS = [
    "speech-2.8-hd",
    "speech-2.8-turbo",
    "speech-2.6-hd",
    "speech-2.6-turbo",
    "speech-02-hd",
    "speech-02-turbo",
    "speech-01-hd",
    "speech-01-turbo",
]
EXPECTED_ENDPOINTS = ["https://api.minimax.io/v1/t2a_v2", "https://api.minimaxi.com/v1/t2a_v2"]


class MiniMaxTextToSpeechTest(unittest.TestCase):
    def setUp(self):
        self.processor = object.__new__(MiniMaxTextToSpeechProcessor)
        self.processor._input = TextToSpeechInput(input_text="Hello world.")
        self.processor._config = TextToSpeechConfiguration(voice_setting={"voice_id": "test-voice"})
        self.provider = MiniMaxProviderConfig(api_key="test-key")
        self.processor.get_provider_config = Mock(return_value=self.provider)
        self.asset = Mock(objref="objref://sessionfiles/audio")
        self.processor._create_asset_stream = Mock(return_value=self.asset)
        self.output = SimpleNamespace(
            write=AsyncMock(), finalize=Mock(return_value={"audio_content": self.asset.objref})
        )
        self.processor._output_stream = self.output
        self.response = Mock()
        self.response.json.return_value = {
            "base_resp": {"status_code": 0},
            "data": {"status": 2, "audio": b"audio bytes".hex()},
        }

    def test_registration_and_processor_discovery(self):
        registrations = [provider for provider in PROVIDERS if provider["slug"] == "minimax"]
        self.assertEqual(len(registrations), 1)
        self.assertEqual(
            registrations[0]["config_schema"], "llmstack.processors.providers.minimax.MiniMaxProviderConfig"
        )
        processors = get_all_sub_classes(registrations[0]["processor_packages"][0], ApiProcessorInterface)
        self.assertIn(MiniMaxTextToSpeechProcessor, processors)
        self.assertIs(ProcessorFactory.get_processor("text_to_speech", "minimax"), MiniMaxTextToSpeechProcessor)
        self.assertEqual(MiniMaxProviderConfig.get_config_schema()["properties"]["api_key"]["widget"], "password")

    @patch("llmstack.processors.providers.minimax.tts.requests.post")
    def test_both_regions_and_all_models(self, post):
        post.return_value = self.response
        schema = TextToSpeechConfiguration.model_json_schema()
        self.assertEqual(schema["properties"]["model"]["default"], "speech-2.8-hd")
        self.assertEqual(schema["properties"]["model"]["enum"], EXPECTED_MODELS)
        self.assertEqual(
            MiniMaxProviderConfig.model_json_schema()["properties"]["speech_api_url"]["enum"], EXPECTED_ENDPOINTS
        )
        for endpoint in EXPECTED_ENDPOINTS:
            for model in EXPECTED_MODELS:
                with self.subTest(endpoint=endpoint, model=model):
                    self.provider.speech_api_url = endpoint
                    self.processor._config.model = model
                    result = self.processor.process()
                    self.assertEqual(result, {"audio_content": self.asset.objref})
                    args, kwargs = post.call_args
                    self.assertEqual(args, (endpoint,))
                    self.assertEqual(kwargs["headers"], {"Authorization": "Bearer test-key"})
                    self.assertEqual(kwargs["timeout"], 120)
                    self.assertFalse(kwargs["allow_redirects"])
                    self.assertEqual(kwargs["json"]["model"], model)
                    self.assertEqual(kwargs["json"]["text"], "Hello world.")
                    self.assertFalse(kwargs["json"]["stream"])
                    self.assertEqual(kwargs["json"]["output_format"], "hex")
                    self.assertNotIn("language_boost", kwargs["json"])
                    self.processor.get_provider_config.assert_called_with(model_slug=model)
                    self.asset.append_chunk.assert_called_with(b"audio bytes")
                    self.asset.finalize.assert_called_with()
                    self.assertEqual(self.output.write.call_args.args[0].audio_content, self.asset.objref)

    @patch("llmstack.processors.providers.minimax.tts.requests.post")
    def test_optional_parameters_and_subtitle_output(self, post):
        post.return_value = self.response
        self.response.json.return_value["data"]["subtitle_file"] = "https://example.com/subtitles.json"
        self.processor._config = TextToSpeechConfiguration(
            voice_setting={"voice_id": "test-voice", "speed": 1.2, "vol": 2, "pitch": 3},
            audio_setting={"format": "wav", "sample_rate": 44100, "channel": 2},
            language_boost="auto",
            pronunciation_dict={"tone": ["API/A P I"]},
            voice_modify={"pitch": 10, "sound_effects": "robotic"},
            subtitle_enable=True,
        )
        self.processor.process()
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["voice_setting"], {"voice_id": "test-voice", "speed": 1.2, "vol": 2, "pitch": 3})
        self.assertEqual(payload["audio_setting"]["format"], "wav")
        self.assertEqual(payload["language_boost"], "auto")
        self.assertEqual(payload["pronunciation_dict"], {"tone": ["API/A P I"]})
        self.assertEqual(payload["voice_modify"], {"pitch": 10, "sound_effects": "robotic"})
        self.assertTrue(payload["subtitle_enable"])
        self.assertEqual(self.output.write.call_args.args[0].subtitle_url, "https://example.com/subtitles.json")

    @patch("llmstack.processors.providers.minimax.tts.requests.post")
    def test_audio_formats_use_matching_asset_media_types(self, post):
        post.return_value = self.response
        for audio_format, mime_type in {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "pcm": "audio/pcm",
        }.items():
            with self.subTest(audio_format=audio_format):
                self.processor._config.audio_setting.format = audio_format
                self.processor.process()
                self.processor._create_asset_stream.assert_called_with(
                    mime_type=mime_type, file_name=f"speech.{audio_format}"
                )
                self.assertEqual(self.output.write.call_args.args[0].mime_type, mime_type)

    @patch("llmstack.processors.providers.minimax.tts.requests.post")
    def test_errors_and_invalid_audio_never_create_assets(self, post):
        post.return_value = self.response
        responses = [
            [],
            {},
            {"base_resp": {"status_code": 1004}, "data": None},
            {"base_resp": {"status_code": 0}, "data": None},
            {"base_resp": {"status_code": 0}, "data": {"status": 1, "audio": "00"}},
            *(
                {"base_resp": {"status_code": 0}, "data": {"status": 2, "audio": audio}}
                for audio in (None, "", " ", "bad", "zz", 123)
            ),
        ]
        for response in responses:
            with self.subTest(response=response):
                self.response.json.return_value = response
                with self.assertRaises(ValueError):
                    self.processor.process()
                self.processor._create_asset_stream.assert_not_called()
                self.output.write.assert_not_called()

    @patch("llmstack.processors.providers.minimax.tts.requests.post")
    def test_http_failure_is_propagated(self, post):
        post.return_value = self.response
        self.response.raise_for_status.side_effect = requests.HTTPError("Request failed")
        with self.assertRaises(requests.HTTPError):
            self.processor.process()
        self.response.json.assert_not_called()
        self.processor._create_asset_stream.assert_not_called()

    def test_invalid_request_configuration(self):
        for config in (
            {"voice_setting": {"voice_id": ""}},
            {"voice_setting": {"voice_id": "test-voice", "speed": 3}},
            {"voice_setting": {"voice_id": "test-voice", "vol": 0}},
            {"voice_setting": {"voice_id": "test-voice"}, "audio_setting": {"format": "pcm"}, "voice_modify": {}},
            {"voice_setting": {"voice_id": "test-voice"}, "model": "invalid"},
        ):
            with self.subTest(config=config), self.assertRaises(ValidationError):
                TextToSpeechConfiguration(**config)
        with self.assertRaises(ValidationError):
            TextToSpeechInput(input_text="")
        with self.assertRaises(ValidationError):
            MiniMaxProviderConfig(speech_api_url="https://example.com")


if __name__ == "__main__":
    unittest.main()
