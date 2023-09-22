import base64
import json
import os
import unittest
from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import UriInput, UriConfiguration, Uri


class UriTextLoaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures_dir = __file__.replace(
            'test_uri.py', '../../../fixtures')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY', 'sk-test')

    def test_data_url_process_txt(self):
        with open(f'{self.fixtures_dir}/sample.txt', 'r') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data.encode('utf-8'))
            mime_type = 'text/plain'
            result = Uri().process(
                input=UriInput(uri=f'data:{mime_type};name=sample.txt;base64,{base64_encoded_data.decode("utf-8")}', env=DataSourceEnvironmentSchema(
                    openai_key=self.openai_api_key)),
                configuration=UriConfiguration()
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(len(result.documents[0].content), 2854)
            self.assertTrue(result.documents[0].content.startswith('Aeque'))
            self.assertTrue(result.documents[0].content.endswith('non erit;'))

            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'text/plain')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.txt')

    def test_data_url_process_csv(self):
        with open(f'{self.fixtures_dir}/sample.csv', 'r') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data.encode('utf-8'))
            mime_type = 'text/csv'
            result = Uri().process(
                input=UriInput(uri=f'data:{mime_type};name=sample.csv;base64,{base64_encoded_data.decode("utf-8")}', env=DataSourceEnvironmentSchema(
                    openai_key=self.openai_api_key)),
                configuration=UriConfiguration()
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(len(result.documents[0].content.split("\n")), 5)
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'text/csv')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.csv')

    def test_data_url_process_rtf(self):
        with open(f'{self.fixtures_dir}/sample.rtf', 'r') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data.encode('utf-8'))
            mime_type = 'text/rtf'
            result = Uri().process(
                input=UriInput(uri=f'data:{mime_type};name=sample.rtf;base64,{base64_encoded_data.decode("utf-8")}', env=DataSourceEnvironmentSchema(
                    openai_key=self.openai_api_key)),
                configuration=UriConfiguration()
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'text/rtf')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.rtf')

    def test_data_url_process_json(self):
        with open(f'{self.fixtures_dir}/sample.json', 'r') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data.encode('utf-8'))
            mime_type = 'application/json'
            result = Uri().process(
                input=UriInput(uri=f'data:{mime_type};name=sample.json;base64,{base64_encoded_data.decode("utf-8")}', env=DataSourceEnvironmentSchema(
                    openai_key=self.openai_api_key)),
                configuration=UriConfiguration()
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(json.loads(
                result.documents[0].content), {"key": "value"})
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'application/json')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.json')

    def test_data_url_process_pdf(self):
        with open(f'{self.fixtures_dir}/sample.pdf', 'rb') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data)
            mime_type = 'application/pdf'
            result = Uri().process(
                input=UriInput(uri=f'data:{mime_type};name=sample.pdf;base64,{base64_encoded_data.decode("utf-8")}', env=DataSourceEnvironmentSchema(
                    openai_key=self.openai_api_key)),
                configuration=UriConfiguration()
            )
            self.assertEqual(len(result.documents), 1)
            self.assertTrue(result.documents[0].content.startswith('Aeque'))
            self.assertTrue(result.documents[0].content.endswith('non erit;'))
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'application/pdf')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.pdf')

    def test_http_url_process_pdf(self):
        result = Uri().process(
            input=UriInput(
                uri='https://arxiv.org/pdf/1706.03762.pdf', env=None),
            configuration=UriConfiguration()
        )
        self.assertTrue(len(result.documents) > 0)
        self.assertEqual(
            result.documents[0].metadata['mime_type'], 'application/pdf')
        self.assertEqual(
            result.documents[0].metadata['file_name'], 'https://arxiv.org/pdf/1706.03762.pdf')

    def test_http_url_process_html(self):
        result = Uri().process(
            input=UriInput(uri='http://example.com', env=None),
            configuration=UriConfiguration()
        )
        self.assertTrue(len(result.documents) > 0)


if __name__ == '__main__':
    unittest.main()
