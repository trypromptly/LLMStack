import base64
import json
import os
import unittest

from common.promptly.blocks.data_extracter.aws_s3_bucket import AWSS3BucketDataExtractorBlock
from common.promptly.blocks.data_extracter.aws_s3_path import AWSS3PathDataExtractorBlock
from common.promptly.blocks.data_transformer import DataTransformerProcessor
from common.promptly.blocks.data_transformer import DataTransformerProcessorInput
from common.promptly.blocks.http import HttpAPIProcessor
from common.promptly.blocks.http import HttpAPIProcessorOutput
from common.promptly.blocks.python_code_executor import PythonCodeExecutorProcessor
from common.promptly.blocks.vendor.huggingface import HuggingfaceEndpointProcessor
from common.promptly.blocks.vendor.openai import OpenAIAudioTranscriptionProcessor
from common.promptly.blocks.vendor.openai import OpenAIAudioTranslationsProcessor
from common.promptly.blocks.vendor.openai import OpenAIChatCompletionsAPIProcessor
from common.promptly.blocks.vendor.openai import OpenAICompletionsAPIProcessor
from common.promptly.blocks.vendor.openai import OpenAIFile
from common.promptly.blocks.vendor.openai import OpenAIImageGenerationsProcessor


class TestHttpProcessor(unittest.TestCase):
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


class TestOpenAIProcessor(unittest.TestCase):
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
        # self.assertIn("usage", output.metadata.raw_response)

    def test_name_audio_transcription(self):
        self.assertEqual(
            OpenAIAudioTranscriptionProcessor.name(),
            'openai_audio_transcription_processor',
        )

    def test_valid_audio_transcription(self):
        with open('/Users/vigneshaigal/Downloads/HIN_M_AbhishekS.mp3', 'rb') as f:

            audio_file = OpenAIFile(
                name='HIN_M_AbhishekS.mp3', content=f.read(), mime_type='application/octet-stream',
            )
            output = OpenAIAudioTranscriptionProcessor(
                configuration={'model': 'whisper-1', 'response_format': 'json'},
            ).process(
                    {
                        'file': audio_file.dict(),
                        'env': {'openai_api_key': self.api_key},
                    },
            )
            self.assertGreater(len(output.text), 0)

    def test_name_audio_translation(self):
        self.assertEqual(
            OpenAIAudioTranslationsProcessor.name(),
            'openai_audio_translation_processor',
        )

    def test_valid_audio_translation(self):
        with open('/Users/vigneshaigal/Downloads/HIN_M_AbhishekS.mp3', 'rb') as f:

            audio_file = OpenAIFile(
                name='HIN_M_AbhishekS.mp3', content=f.read(), mime_type='application/octet-stream',
            )

            output = OpenAIAudioTranslationsProcessor(
                configuration={'model': 'whisper-1', 'response_format': 'json'},
            ).process(
                    {
                        'file': audio_file.dict(),
                        'env': {'openai_api_key': self.api_key},
                    },
            )
            self.assertGreater(len(output.text), 0)


class TestDataTransformaerProcessor(unittest.TestCase):
    def test_valid_data_transformer(self):
        input_str = '{"id":1, "name":"FooBar"}'
        input = DataTransformerProcessorInput(input=json.loads(input_str))
        result = DataTransformerProcessor(
            configuration={'mapper': {'username': '$.name'}},
        ).process(input=input.dict()).output
        self.assertEqual(result['username'], 'FooBar')

    def test_invalid_data_transformer(self):
        input_str = '{"id":1, "name":"FooBar"}'
        input = DataTransformerProcessorInput(input=json.loads(input_str))
        result = DataTransformerProcessor(
            configuration={'mapper': {'username': '$.name1'}},
        ).process(input=input.dict()).output
        self.assertEqual(result['username'], None)


class TestPythonCodeExecutorProcessor(unittest.TestCase):
    def test_valid_python_code_executor(self):
        code = """def python_code_executor_transform(**kwargs):
                    return kwargs['data']
               """
        result = PythonCodeExecutorProcessor(
            configuration={
            'python_function_code': code,
            },
        ).process(input={'inputs': [{'key': 'data', 'value': 'test'}], 'function_name': 'python_code_executor_transform'})

        self.assertEqual(result.output, 'test')


class TestHuggingfaceEndpointProcessor(unittest.TestCase):
    def test_valid_hugging_face(self):
        import json
        api_key = os.environ.get('HF_API_KEY')
        result = HuggingfaceEndpointProcessor(
            configuration={
                'endpoint_url': 'https://api-inference.huggingface.co/models/bert-base-uncased',
            },
        ).process(input={'env': {'huggingfacehub_api_key': api_key}, 'inputs': json.dumps({'inputs': 'The answer to the universe is [MASK].'})})

        print(result)


class TestAWSS3PathDataExtractorBlock(unittest.TestCase):
    def test_valid_aws_s3_path(self):
        AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

        result = AWSS3PathDataExtractorBlock(
            configuration={
            'aws_access_key_id': AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
            },
        ).process(
            input={'bucket': 'makerdojotest', 'path': 'test_shopify.csv'},
        )
        self.assertGreater(len(result.result.content), 0)

        for row in AWSS3PathDataExtractorBlock(configuration={}).process_iter(
            input={
                'bucket': 'makerdojotest', 'path': 'test_shopify.csv',
            },
        ):
            self.assertGreater(len(row.result.content), 0)

    def test_invalid_aws_s3_path(self):
        with self.assertRaises(Exception) as context:
            result = AWSS3PathDataExtractorBlock(configuration={}).process(
                input={
                    'bucket': 'makerdojo', 'path': 'as.csv',
                },
            )


class TestAWSS3BucketDataExtractorBlock(unittest.TestCase):
    def test_valid_aws_s3_block(self):
        result = AWSS3BucketDataExtractorBlock(configuration={}).process(
            input={
                'bucket': 'makerdojotest',
            },
        )
        self.assertGreater(len(result.data[0].content), 0)

        for row in AWSS3BucketDataExtractorBlock(configuration={}).process_iter(
            input={
                'bucket': 'makerdojotest',
            },
        ):
            self.assertGreater(len(row.data[0].content), 0)


if __name__ == '__main__':
    unittest.main()
