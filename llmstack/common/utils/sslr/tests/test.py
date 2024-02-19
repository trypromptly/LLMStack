import os
import unittest

from llmstack.common.utils.sslr import LLM
from llmstack.common.utils.sslr.constants import (
    PROVIDER_GOOGLE,
    PROVIDER_OPENAI,
    PROVIDER_STABILITYAI,
)

PROVIDER_MODEL_MAP = {
    PROVIDER_GOOGLE: "gemini-pro",
    PROVIDER_OPENAI: "gpt-3.5-turbo",
}


class TestLLM(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
        )

    def test_models(self):
        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI, PROVIDER_STABILITYAI]:
            client = self._initialize_client(provider)
            print(client.models.list())

    def test_chat_completions_single_text(self):
        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI]:
            client = self._initialize_client(provider)
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Say this is a test",
                    }
                ],
                model=PROVIDER_MODEL_MAP[provider],
                max_tokens=100,
            )
            for choice in result.choices:
                self.assertIsNotNone(choice.message.content_str)

    def test_chat_completions_multiple_parts(self):
        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI]:
            client = self._initialize_client(provider)
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "mime_type": "text/plain", "data": "Say this is "},
                            {"type": "text", "mime_type": "text/plain", "data": "a test"},
                        ],
                    },
                ],
                model=PROVIDER_MODEL_MAP[provider],
                max_tokens=100,
            )
            for choice in result.choices:
                self.assertIsNotNone(choice.message.content_str)

    def test_chat_completions_single_text_streaming(self):
        import openai

        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI]:
            client = self._initialize_client(provider)
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Say this is a test",
                    }
                ],
                model=PROVIDER_MODEL_MAP[provider],
                max_tokens=100,
                stream=True,
            )
            self.assertIsInstance(result, openai.Stream)
            for chunk in result:
                if chunk.choices[0].finish_reason is None:
                    self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_multiple_parts_streaming(self):
        import openai

        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI]:
            client = self._initialize_client(provider)
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "mime_type": "text/plain", "data": "Say this is "},
                            {"type": "text", "mime_type": "text/plain", "data": "a test"},
                        ],
                    },
                ],
                model=PROVIDER_MODEL_MAP[provider],
                max_tokens=100,
                stream=True,
            )
            self.assertIsInstance(result, openai.Stream)
            for chunk in result:
                if chunk.choices[0].finish_reason is None:
                    self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_completions_function_calling(self):
        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI]:
            client = self._initialize_client(provider)
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "What's the weather like in San Francisco?",
                    }
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_current_weather",
                            "description": "Get the current weather in a given location",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "The city and state, e.g. San Francisco, CA",
                                    },
                                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                                },
                                "required": ["location"],
                            },
                        },
                    }
                ],
                model=PROVIDER_MODEL_MAP[provider],
                stream=False,
                n=1,
                max_tokens=200,
            )

            for choice in result.choices:
                self.assertIsNotNone(choice.message.tool_calls_list)
                self.assertEqual(len(choice.message.tool_calls_list), 1)

    def test_completions_function_calling_streaming(self):
        import openai

        for provider in [PROVIDER_GOOGLE, PROVIDER_OPENAI]:
            client = self._initialize_client(provider)
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "What's the weather like in San Francisco?",
                    }
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_current_weather",
                            "description": "Get the current weather in a given location",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "The city and state, e.g. San Francisco, CA",
                                    },
                                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                                },
                                "required": ["location"],
                            },
                        },
                    }
                ],
                model=PROVIDER_MODEL_MAP[provider],
                stream=True,
                n=1,
                max_tokens=200,
            )
            self.assertIsInstance(result, openai.Stream)

            function_names = [""] * 100
            function_args = [""] * 100
            for chunk in result:
                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        if tool_call.function and tool_call.function.name:
                            function_names[tool_call.index] += tool_call.function.name
                        if tool_call.function and tool_call.function.arguments:
                            function_args[tool_call.index] += tool_call.function.arguments

            function_names = list(filter(lambda entry: entry != "", function_names))
            function_args = list(filter(lambda entry: entry != "", function_args))
            self.assertEqual(function_names, ["get_current_weather"])
            self.assertGreater(len(function_args[0]), 1)


if __name__ == "__main__":
    unittest.main()
