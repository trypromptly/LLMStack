import unittest
import json
import os

from llmstack.common.blocks.llm.huggingface import HuggingfaceEndpointProcessor


class HuggingfaceEndpointProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get('HF_API_KEY')

    def test_name_valid(self):
        self.assertEqual(
            HuggingfaceEndpointProcessor.name(),
            'huggingface_endpoint_processor',
        )

    def test_process_valid(self):
        result = HuggingfaceEndpointProcessor(
            configuration={
                'endpoint_url': 'https://api-inference.huggingface.co/models/bert-base-uncased',
            },
        ).process(
            input={
                'env': {
                    'huggingfacehub_api_key': self.api_key},
                'inputs': json.dumps(
                    {
                        'inputs': 'The answer to the universe is [MASK].'})})
        self.assertTrue(len(json.loads(result.result)) > 0)


if __name__ == '__main__':
    unittest.main()
