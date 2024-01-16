import unittest
import os
from llmstack.common.blocks.llm.openai import OpenAIChatCompletionsAPIProcessor


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


if __name__ == '__main__':
    unittest.main()
