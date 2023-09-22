import unittest
import os
from llmstack.common.blocks.llm.openai import OpenAIChatCompletionsAPIProcessor, OpenAICompletionsAPIProcessor, OpenAIImageGenerationsProcessor, OpenAIAudioTranscriptionProcessor, OpenAIAudioTranslationsProcessor


class OpenAIChatCompletionsAPIProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get('OPENAI_API_KEY')

    def test_name_chat_completions(self):
        self.assertEqual(
            OpenAIChatCompletionsAPIProcessor.name(),
            'openai_chat_completions_api_processor',
        )

    def test_valid_chat_completions(self):
        output = OpenAIChatCompletionsAPIProcessor(
            configuration={'model': 'gpt-3.5-turbo'},
        ).process(
            {
                'system_message': '',
                'messages': [{'role': 'user', 'content': 'Repeat word'}],
                'env': {'openai_api_key': self.api_key},
            },
        )
        self.assertGreater(len(output.choices), 0)
        self.assertIn('usage', output.metadata.raw_response)

    def test_valid_chat_completions_streaming(self):
        output_iter = OpenAIChatCompletionsAPIProcessor(
            configuration={'model': 'gpt-3.5-turbo', 'stream': True},
        ).process_iter(
            {
                'system_message': '',
                'messages': [{'role': 'user', 'content': 'Repeat word'}],
                'env': {'openai_api_key': self.api_key},
            },
        )
        for result in output_iter:
            self.assertGreater(len(result.choices), 0)

    def test_invalid_chat_completions_with_history(self):
        output = OpenAIChatCompletionsAPIProcessor(
            configuration={'model': 'gpt-3.5-turbo'},
        ).process(
            {
                'system_message': '',
                'chat_history': [{'role': 'user', 'content': 'Repeat word ice'}],
                'messages': [{'role': 'user', 'content': 'What is the repeated word ?'}],
                'env': {'openai_api_key': self.api_key},
            },
        )
        self.assertIn('ice', output.choices[0].content.lower())


class OpenAICompletionsAPIProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get('OPENAI_API_KEY')

    def test_name_completions(self):
        self.assertEqual(
            OpenAICompletionsAPIProcessor.name(),
            'openai_completions_api_processor',
        )

    def test_valid_completions(self):
        output = OpenAICompletionsAPIProcessor(
            configuration={'model': 'text-davinci-003'},
        ).process(input={'prompt': 'Repeat the word ice', 'env': {'openai_api_key': self.api_key}})
        self.assertGreater(len(output.choices), 0)
        self.assertIn('usage', output.metadata.raw_response)

    def test_invalid_completions(self):
        with self.assertRaises(Exception) as context:
            OpenAICompletionsAPIProcessor(
                configuration={'model': 'text-davinci-003'},
            ).process(input={'prompt': 'Repeat the word ice', 'env': {'openai_api_key': 'invalid_key'}})

    def test_valid_completions_streaming(self):
        output_iter = OpenAICompletionsAPIProcessor(
            configuration={'model': 'text-davinci-003', 'stream': True},
        ).process_iter(input={'prompt': 'Repeat the word ice', 'env': {'openai_api_key': self.api_key}})
        for entry in output_iter:
            self.assertGreater(len(entry.choices), 0)


class OpenAIImageGenerationsProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get('OPENAI_API_KEY')

    def test_name_image_generations(self):
        self.assertEqual(
            OpenAIImageGenerationsProcessor.name(),
            'openai_image_generations_processor',
        )

    def test_valid_image_generations(self):
        output = OpenAIImageGenerationsProcessor(
            configuration={'n': 1},
        ).process(
            {
                'prompt': 'A dog',
                'env': {'openai_api_key': self.api_key},
            },
        )

        self.assertGreater(len(output.answer), 0)


class OpenAIAudioTranscriptionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get('OPENAI_API_KEY')

    def test_name_audio_transcriptions(self):
        self.assertEqual(
            OpenAIAudioTranscriptionProcessor.name(),
            'openai_audio_transcription_processor',
        )


class OpenAIAudioTranslationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get('OPENAI_API_KEY')

    def test_name_audio_translations(self):
        self.assertEqual(
            OpenAIAudioTranslationsProcessor.name(),
            'openai_audio_translation_processor')


if __name__ == '__main__':
    unittest.main()
