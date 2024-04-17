import os
import unittest

from llmstack.common.utils.sslr import LLM
from llmstack.common.utils.sslr.constants import (
    PROVIDER_ANTHROPIC,
    PROVIDER_COHERE,
    PROVIDER_GOOGLE,
    PROVIDER_MISTRAL,
    PROVIDER_OPENAI,
    PROVIDER_STABILITYAI,
)

PROVIDER_MODEL_MAP = {
    PROVIDER_GOOGLE: "gemini-pro",
    PROVIDER_OPENAI: "gpt-3.5-turbo",
    PROVIDER_ANTHROPIC: "claude-2.1",
    PROVIDER_COHERE: "command",
    PROVIDER_MISTRAL: "mistral-small-latest",
}


IMAGE_GENERATION_PROVIDER_MODEL_MAP = {
    PROVIDER_OPENAI: "dall-e-2",
    PROVIDER_STABILITYAI: "stable-diffusion-xl-1024-v1-0",
}

MAX_TOKENS = 50


class TestLLMModels(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
            anthropic_api_key=os.environ.get("DEFAULT_ANTHROPIC_KEY"),
            cohere_api_key=os.environ.get("DEFAULT_COHERE_KEY"),
        )

    def test_openai_models(self):
        client = self._initialize_client(PROVIDER_OPENAI)
        model_ids = [model.id for model in client.models.list()]
        self.assertTrue(len(model_ids) > 0)

    def test_google_models(self):
        client = self._initialize_client(PROVIDER_GOOGLE)
        model_ids = [model.id for model in client.models.list()]
        self.assertTrue(len(model_ids) > 0)

    def test_stabilityai_models(self):
        client = self._initialize_client(PROVIDER_STABILITYAI)
        model_ids = [model.id for model in client.models.list()]
        self.assertTrue(len(model_ids) > 0)

    def test_cohere_models(self):
        client = self._initialize_client(PROVIDER_COHERE)
        model_ids = [model.id for model in client.models.list()]
        self.assertTrue(len(model_ids) > 0)


COMPLETIONS_PROVIDER_LIST = [PROVIDER_OPENAI, PROVIDER_GOOGLE, PROVIDER_COHERE]
COMPLETIONS_WITH_FN_PROVIDER_LIST = [PROVIDER_OPENAI, PROVIDER_GOOGLE]


class TestLLMChatCompletions(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
            anthropic_api_key=os.environ.get("DEFAULT_ANTHROPIC_KEY"),
            cohere_api_key=os.environ.get("DEFAULT_COHERE_KEY"),
            mistral_api_key=os.environ.get("DEFAULT_MISTRAL_KEY"),
        )

    def _call_chat_completions_single_text(self, provider, model):
        client = self._initialize_client(provider)
        result = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model=model,
            max_tokens=MAX_TOKENS,
        )
        return result

    def test_chat_completions_single_text_openai(self):
        result = self._call_chat_completions_single_text(PROVIDER_OPENAI, PROVIDER_MODEL_MAP[PROVIDER_OPENAI])
        self.assertIsNotNone(result.choices[0].message.content_str)

    def test_chat_completions_single_text_google(self):
        result = self._call_chat_completions_single_text(PROVIDER_GOOGLE, PROVIDER_MODEL_MAP[PROVIDER_GOOGLE])
        self.assertIsNotNone(result.choices[0].message.content_str)

    def test_chat_completions_single_text_cohere(self):
        result = self._call_chat_completions_single_text(PROVIDER_COHERE, PROVIDER_MODEL_MAP[PROVIDER_COHERE])
        self.assertIsNotNone(result.choices[0].message.content_str)

    def test_chat_completions_single_text_anthropic(self):
        result = self._call_chat_completions_single_text(PROVIDER_ANTHROPIC, PROVIDER_MODEL_MAP[PROVIDER_ANTHROPIC])
        self.assertIsNotNone(result.choices[0].message.content_str)

    def test_chat_completions_single_text_mistral(self):
        result = self._call_chat_completions_single_text(PROVIDER_MISTRAL, PROVIDER_MODEL_MAP[PROVIDER_MISTRAL])
        self.assertIsNotNone(result.choices[0].message.content_str)

    def _call_chat_completions_multiple_parts(self, provider, model):
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
            model=model,
            max_tokens=MAX_TOKENS,
        )
        return result

    def test_chat_completions_multiple_parts_openai(self):
        result = self._call_chat_completions_multiple_parts(PROVIDER_OPENAI, PROVIDER_MODEL_MAP[PROVIDER_OPENAI])
        for choice in result.choices:
            self.assertIsNotNone(choice.message.content_str)

    def test_chat_completions_multiple_parts_google(self):
        result = self._call_chat_completions_multiple_parts(PROVIDER_GOOGLE, PROVIDER_MODEL_MAP[PROVIDER_GOOGLE])
        for choice in result.choices:
            self.assertIsNotNone(choice.message.content_str)

    def test_chat_completions_multiple_parts_cohere(self):
        result = self._call_chat_completions_multiple_parts(PROVIDER_COHERE, PROVIDER_MODEL_MAP[PROVIDER_COHERE])
        for choice in result.choices:
            self.assertIsNotNone(choice.message.content_str)

    def test_chat_completions_multiple_parts_anthropic(self):
        result = self._call_chat_completions_multiple_parts(PROVIDER_ANTHROPIC, PROVIDER_MODEL_MAP[PROVIDER_ANTHROPIC])
        for choice in result.choices:
            self.assertIsNotNone(choice.message.content_str)


class TestLLMChatCompletionsStreaming(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
            anthropic_api_key=os.environ.get("DEFAULT_ANTHROPIC_KEY"),
            cohere_api_key=os.environ.get("DEFAULT_COHERE_KEY"),
            mistral_api_key=os.environ.get("DEFAULT_MISTRAL_KEY"),
        )

    def _call_chat_completions_single_text_streaming(self, provider, model):
        client = self._initialize_client(provider)
        result = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model=model,
            max_tokens=MAX_TOKENS,
            stream=True,
        )
        return result

    def test_chat_completions_single_text_streaming_openai(self):
        import openai

        result = self._call_chat_completions_single_text_streaming(PROVIDER_OPENAI, PROVIDER_MODEL_MAP[PROVIDER_OPENAI])
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_single_text_streaming_google(self):
        import openai

        result = self._call_chat_completions_single_text_streaming(PROVIDER_GOOGLE, PROVIDER_MODEL_MAP[PROVIDER_GOOGLE])
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_single_text_streaming_cohere(self):
        import openai

        result = self._call_chat_completions_single_text_streaming(PROVIDER_COHERE, PROVIDER_MODEL_MAP[PROVIDER_COHERE])
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_single_text_streaming_anthropic(self):
        import openai

        result = self._call_chat_completions_single_text_streaming(
            PROVIDER_ANTHROPIC, PROVIDER_MODEL_MAP[PROVIDER_ANTHROPIC]
        )
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_single_text_streaming_mistral(self):
        import openai

        result = self._call_chat_completions_single_text_streaming(
            PROVIDER_MISTRAL, PROVIDER_MODEL_MAP[PROVIDER_MISTRAL]
        )
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def _call_chat_completions_multiple_parts_streaming(self, provider, model):
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
            model=model,
            max_tokens=MAX_TOKENS,
            stream=True,
        )
        return result

    def test_chat_completions_multiple_parts_streaming_openai(self):
        import openai

        result = self._call_chat_completions_multiple_parts_streaming(
            PROVIDER_OPENAI, PROVIDER_MODEL_MAP[PROVIDER_OPENAI]
        )
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_multiple_parts_streaming_google(self):
        import openai

        result = self._call_chat_completions_multiple_parts_streaming(
            PROVIDER_GOOGLE, PROVIDER_MODEL_MAP[PROVIDER_GOOGLE]
        )
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_multiple_parts_streaming_cohere(self):
        import openai

        result = self._call_chat_completions_multiple_parts_streaming(
            PROVIDER_COHERE, PROVIDER_MODEL_MAP[PROVIDER_COHERE]
        )
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)

    def test_chat_completions_multiple_parts_streaming_anthropic(self):
        import openai

        result = self._call_chat_completions_multiple_parts_streaming(
            PROVIDER_ANTHROPIC, PROVIDER_MODEL_MAP[PROVIDER_ANTHROPIC]
        )
        self.assertIsInstance(result, openai.Stream)
        for chunk in result:
            if chunk.choices[0].finish_reason is None:
                self.assertIsNotNone(chunk.choices[0].delta.content_str)


class TestLLMChatFunctionCalling(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
            anthropic_api_key=os.environ.get("DEFAULT_ANTHROPIC_KEY"),
            cohere_api_key=os.environ.get("DEFAULT_COHERE_KEY"),
        )

    def test_completions_function_calling(self):
        for provider in COMPLETIONS_WITH_FN_PROVIDER_LIST:
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

            self.assertEqual(len(result.choices[0].message.tool_calls), 1)
            self.assertEqual(result.choices[0].message.tool_calls[0].function.name, "get_current_weather")
            self.assertGreater(len(result.choices[0].message.tool_calls[0].function.arguments), 1)

    def test_completions_function_calling_streaming(self):
        import openai

        for provider in COMPLETIONS_WITH_FN_PROVIDER_LIST:
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


IMAGE_GENERATION_PROVIDER_LIST = [PROVIDER_OPENAI, PROVIDER_STABILITYAI]


class TestLLMImageGeneration(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
            anthropic_api_key=os.environ.get("DEFAULT_ANTHROPIC_KEY"),
            cohere_api_key=os.environ.get("DEFAULT_COHERE_KEY"),
        )

    def _call_image_generation(self, provider, model):
        client = self._initialize_client(provider)
        result = client.images.generate(
            prompt="a cat in the style of a dog",
            model=model,
            n=1,
            response_format="b64_json",
            size="1024x1024",
        )
        return result

    def test_image_generation_openai(self):
        result = self._call_image_generation(PROVIDER_OPENAI, IMAGE_GENERATION_PROVIDER_MODEL_MAP[PROVIDER_OPENAI])
        assert len(result.data) == 1
        assert result.data[0].b64_json is not None

    def test_image_generation_stabilityai(self):
        result = self._call_image_generation(
            PROVIDER_STABILITYAI, IMAGE_GENERATION_PROVIDER_MODEL_MAP[PROVIDER_STABILITYAI]
        )
        assert len(result.data) == 1
        assert result.data[0].b64_json is not None


class TestLLMImageEdit(unittest.TestCase):
    def _initialize_client(self, provider):
        return LLM(
            provider=provider,
            openai_api_key=os.environ.get("DEFAULT_OPENAI_KEY"),
            stabilityai_api_key=os.environ.get("DEFAULT_STABILITYAI_KEY"),
            google_api_key=os.environ.get("DEFAULT_GOOGLE_KEY"),
            anthropic_api_key=os.environ.get("DEFAULT_ANTHROPIC_KEY"),
            cohere_api_key=os.environ.get("DEFAULT_COHERE_KEY"),
        )

    def test_image_edit_stabilityai(self):
        import pathlib

        image_file = f"{pathlib.Path(__file__).parent.resolve()}/test_image.jpg"
        with open(image_file, "rb"):
            client = self._initialize_client(PROVIDER_STABILITYAI)
            result = client.images.edit(image="resized_image_file_data", model="core", operation="remove_background")
            print(result)


if __name__ == "__main__":
    unittest.main()
