import json
import unittest
from datetime import timedelta

import httpx

from llmstack.common.utils.sslr.resources.chat.completions import (
    _convert_to_anthropic_format,
)
from llmstack.processors.providers.minimax import MiniMaxProviderConfig
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


if __name__ == "__main__":
    unittest.main()
