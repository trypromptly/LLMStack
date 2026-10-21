import json
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from pydantic import ValidationError

from llmstack.common.utils.sslr.resources.chat.completions import (
    _convert_to_anthropic_format,
)
from llmstack.processors.providers.minimax import MiniMaxProviderConfig
from llmstack.processors.providers.minimax.chat_completions import (
    MessagesConfiguration,
    MessagesInput,
    MessagesOutput,
    MessagesProcessor,
)
from llmstack.processors.providers.minimax.client import create_minimax_client


class MiniMaxProviderTest(unittest.TestCase):
    def test_provider_schema_lists_all_supported_endpoints(self):
        description = MiniMaxProviderConfig.model_fields["base_url"].description

        self.assertIn("https://api.minimax.io/v1", description)
        self.assertIn("https://api.minimaxi.com/v1", description)
        self.assertIn("https://api.minimax.io/anthropic", description)
        self.assertIn("https://api.minimaxi.com/anthropic", description)

    def test_client_routes_all_supported_endpoints(self):
        cases = (
            ("https://api.minimax.io/v1", "https://api.minimax.io/v1/chat/completions", "openai"),
            ("https://api.minimaxi.com/v1", "https://api.minimaxi.com/v1/chat/completions", "openai"),
            ("https://api.minimax.io/anthropic", "https://api.minimax.io/anthropic/v1/messages", "anthropic"),
            (
                "https://api.minimaxi.com/anthropic",
                "https://api.minimaxi.com/anthropic/v1/messages",
                "anthropic",
            ),
        )

        for base_url, expected_url, protocol in cases:
            with self.subTest(base_url=base_url):
                captured_request = None

                def handler(request):
                    nonlocal captured_request
                    captured_request = request
                    if protocol == "anthropic":
                        response = httpx.Response(
                            200,
                            json={
                                "id": "msg_test",
                                "type": "message",
                                "role": "assistant",
                                "model": "MiniMax-M3",
                                "content": [{"type": "text", "text": "ok"}],
                                "stop_reason": "end_turn",
                                "usage": {"input_tokens": 1, "output_tokens": 1},
                            },
                        )
                        response.elapsed = timedelta()
                        return response
                    response = httpx.Response(
                        200,
                        json={
                            "id": "chatcmpl_test",
                            "object": "chat.completion",
                            "created": 0,
                            "model": "MiniMax-M3",
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {"role": "assistant", "content": "ok"},
                                    "finish_reason": "stop",
                                }
                            ],
                            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        },
                    )
                    response.elapsed = timedelta()
                    return response

                http_client = httpx.Client(transport=httpx.MockTransport(handler))
                client = create_minimax_client(
                    MiniMaxProviderConfig(api_key="test-key", base_url=base_url),
                    http_client=http_client,
                )
                try:
                    client.chat.completions.create(
                        messages=[{"role": "user", "content": "Hello"}],
                        model="MiniMax-M3",
                        max_tokens=8,
                        stream=False,
                        extra_body={"thinking": {"type": "adaptive"}},
                    )
                finally:
                    client.close()

                self.assertIsNotNone(captured_request)
                self.assertEqual(str(captured_request.url), expected_url)
                self.assertEqual(json.loads(captured_request.content)["thinking"], {"type": "adaptive"})

    def test_multimodal_content_converts_to_anthropic_blocks(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,aW1hZ2U=",
                            "detail": "high",
                        },
                    },
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": "https://cdn.example.com/video.mp4",
                            "fps": 2,
                        },
                    },
                ],
            }
        ]

        converted = _convert_to_anthropic_format(messages)

        self.assertEqual(
            converted[0]["content"],
            [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "aW1hZ2U=",
                        "detail": "high",
                    },
                },
                {
                    "type": "video",
                    "source": {
                        "type": "url",
                        "url": "https://cdn.example.com/video.mp4",
                        "fps": 2,
                    },
                },
            ],
        )


class _OutputSink:
    def __init__(self):
        self.values = []

    async def write(self, value):
        self.values.append(value)

    def finalize(self):
        return MessagesOutput(result="".join(value.result for value in self.values))


class MiniMaxProcessorTest(unittest.TestCase):
    def test_default_catalog_and_saved_models(self):
        schema = MessagesConfiguration.model_json_schema()["properties"]["model"]
        self.assertEqual(schema["default"], "MiniMax-M3.1-Flash")
        self.assertEqual(schema["options"], ["MiniMax-M3.1-Flash", "MiniMax-M3"])
        self.assertEqual(schema["widget"], "customselect")
        self.assertNotIn("enum", schema)
        for model in ("MiniMax-M3", "MiniMax-M2.7", "MiniMax-M2.1", "saved-custom-model"):
            self.assertEqual(MessagesConfiguration(model=model).model, model)

    def test_model_limits_and_thinking(self):
        for model in ("MiniMax-M3.1-Flash", "MiniMax-M3"):
            self.assertEqual(MessagesConfiguration(model=model, max_tokens=524288).max_tokens, 524288)
            with self.assertRaises(ValidationError):
                MessagesConfiguration(model=model, max_tokens=524289)
        for model in ("MiniMax-M3.1-Flash", "MiniMax-M2.7"):
            with self.assertRaisesRegex(ValidationError, "does not support disabling thinking"):
                MessagesConfiguration(model=model, thinking="disabled")
        with self.assertRaises(ValidationError):
            MessagesConfiguration(reasoning_effort="none")
        self.assertEqual(MessagesConfiguration(model="MiniMax-M3", thinking="disabled").thinking, "disabled")

    def test_processor_serialized_requests(self):
        media = [
            {"type": "text", "text": "Describe this"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,aW1hZ2U=", "detail": "high"}},
            {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4", "fps": 2}},
        ]
        cases = [({}, "MiniMax-M3.1-Flash", "adaptive", "max")]
        cases += [
            ({"reasoning_effort": effort}, "MiniMax-M3.1-Flash", "adaptive", effort)
            for effort in ("low", "medium", "high", "xhigh", "max")
        ]
        cases += [
            ({"model": model, "thinking": thinking}, model, thinking, None)
            for model, thinking in (
                ("MiniMax-M3", "adaptive"),
                ("MiniMax-M3", "disabled"),
                ("MiniMax-M2.7", "adaptive"),
                ("MiniMax-M2.1", "adaptive"),
                ("saved-custom-model", "disabled"),
            )
        ]
        for host in ("api.minimax.io", "api.minimaxi.com"):
            for protocol in ("openai", "anthropic"):
                for options, model, thinking, effort in cases:
                    with self.subTest(host=host, protocol=protocol, options=options):
                        requests = []

                        def handler(request):
                            requests.append(request)
                            response = httpx.Response(200, headers={"content-type": "text/event-stream"}, content=b"")
                            response.elapsed = timedelta()
                            return response

                        base_url = f"https://{host}/" + ("anthropic/" if protocol == "anthropic" else "v1/")
                        provider = MiniMaxProviderConfig(api_key="test-key", base_url=base_url)
                        client = create_minimax_client(
                            provider, http_client=httpx.Client(transport=httpx.MockTransport(handler))
                        )
                        content = "Hello" if model in ("MiniMax-M2.7", "MiniMax-M2.1") else media
                        processor = SimpleNamespace(
                            _config=MessagesConfiguration(system_prompt="Be helpful", retain_history=True, **options),
                            _input=MessagesInput(messages=[{"role": "user", "message": content}]),
                            _chat_history=[
                                {"role": "user", "message": "Earlier question"},
                                {"role": "assistant", "message": "Earlier answer"},
                            ],
                            get_provider_config=Mock(return_value=provider),
                            _output_stream=_OutputSink(),
                        )
                        try:
                            with patch(
                                "llmstack.processors.providers.minimax.chat_completions.create_minimax_client",
                                return_value=client,
                            ):
                                MessagesProcessor.process(processor)
                        finally:
                            client.close()
                        self.assertEqual(len(requests), 1)
                        request = requests[0]
                        path = "/anthropic/v1/messages" if protocol == "anthropic" else "/v1/chat/completions"
                        self.assertEqual(str(request.url), f"https://{host}{path}")
                        payload = json.loads(request.content)
                        self.assertEqual(payload["model"], model)
                        self.assertEqual(payload["thinking"], {"type": thinking})
                        self.assertTrue(payload["stream"])
                        self.assertEqual(payload["max_tokens"], 256)
                        self.assertNotIn("service_tier", payload)
                        self.assertNotIn("reasoning_split", payload)
                        if effort:
                            if protocol == "anthropic":
                                self.assertEqual(payload["output_config"], {"effort": effort})
                                self.assertNotIn("reasoning_effort", payload)
                            else:
                                self.assertEqual(payload["reasoning_effort"], effort)
                                self.assertNotIn("output_config", payload)
                        else:
                            self.assertNotIn("reasoning_effort", payload)
                            self.assertNotIn("output_config", payload)
                        if protocol == "anthropic":
                            self.assertEqual(payload["system"], "Be helpful")
                            expected = _convert_to_anthropic_format(
                                [
                                    {"role": "user", "content": "Earlier question"},
                                    {"role": "assistant", "content": "Earlier answer"},
                                    {"role": "user", "content": content},
                                ]
                            )
                            self.assertEqual(payload["messages"], expected)
                        else:
                            self.assertEqual(payload["messages"][-1]["content"], content)
                            self.assertEqual(payload["messages"][1]["content"], "Earlier question")
                            self.assertEqual(payload["messages"][2]["content"], "Earlier answer")
                        processor.get_provider_config.assert_called_once_with(model_slug=model)
                        self.assertEqual(processor._chat_history[0]["message"], "Earlier question")
                        self.assertEqual(processor._chat_history[-2]["message"], content)


if __name__ == "__main__":
    unittest.main()
