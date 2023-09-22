import unittest
from llmstack.common.blocks.http import HttpAPIProcessor, HttpAPIProcessorInput, HttpAPIProcessorOutput, HttpAPIProcessorConfiguration


class HttpAPIProcessorTestCase(unittest.TestCase):
    def test_name(self):
        self.assertEqual(HttpAPIProcessor.name(), 'http_api_processor')

    def test_2xx_response(self):
        input = {
            'url': 'https://jsonplaceholder.typicode.com/todos/1',
            'authorization': {},
        }
        output = HttpAPIProcessor(
            configuration={},
        ).process(input=input)
        self.assertEqual(output.code, 200)

    def test_4xx_response(self):
        input = {
            'url': 'https://jsonplaceholder.typicode.com/todos/1000000',
            'authorization': {},
        }
        output = HttpAPIProcessor(
            configuration={},
        ).process(input=input)
        self.assertEqual(output.code, 404)

    def test_error_response(self):
        input = {
            'url': 'https://jsonplaceholder.typicode.io',
            'authorization': {},
        }
        with self.assertRaises(Exception) as context:
            output = HttpAPIProcessor(
                configuration={},
            ).process(input=input)


if __name__ == '__main__':
    unittest.main()
