import json
import unittest
from llmstack.common.blocks.data.text_extractor.local import LocalTextExtractorProcessor
from llmstack.common.blocks.data.text_extractor import TextExtractorInput


class LocalTextExtractorProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures_dir = __file__.replace(
            'test_local.py', '../../../fixtures')

    def test_process_txt(self):
        with open(f'{self.fixtures_dir}/sample.txt', 'r') as file_p:
            file_data = file_p.read().encode('utf-8')
            mime_type = 'text/plain'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.txt'),
                configuration=None
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(len(result.documents[0].content), 2854)
            self.assertTrue(result.documents[0].content.startswith('Aeque'))
            self.assertTrue(result.documents[0].content.endswith('non erit;'))

            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'text/plain')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.txt')

    def test_process_csv(self):
        with open(f'{self.fixtures_dir}/sample.csv', 'r') as file_p:
            file_data = file_p.read()
            mime_type = 'text/csv'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.csv'),
                configuration=None
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(len(result.documents[0].content.split("\n")), 5)
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'text/csv')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.csv')

    def test_process_rtf(self):
        with open(f'{self.fixtures_dir}/sample.rtf', 'r') as file_p:
            file_data = file_p.read()
            mime_type = 'text/rtf'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.rtf'),
                configuration=None
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'text/rtf')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.rtf')

    def test_process_json(self):
        with open(f'{self.fixtures_dir}/sample.json', 'r') as file_p:
            file_data = file_p.read()
            mime_type = 'application/json'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.json'),
                configuration=None
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(json.loads(
                result.documents[0].content), {"key": "value"})
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'application/json')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.json')

    def test_process_pdf(self):
        with open(f'{self.fixtures_dir}/sample.pdf', 'rb') as file_p:
            file_data = file_p.read()
            mime_type = 'application/pdf'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.pdf'),
                configuration=None
            )
            self.assertEqual(len(result.documents), 1)
            self.assertTrue(result.documents[0].content.startswith('Aeque'))
            self.assertTrue(result.documents[0].content.endswith('non erit;'))
            self.assertEqual(
                result.documents[0].metadata['mime_type'], 'application/pdf')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.pdf')

    def test_process_docx(self):
        with open(f'{self.fixtures_dir}/sample.docx', 'rb') as file_p:
            file_data = file_p.read()
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.docx'),
                configuration=None
            )

            self.assertTrue(len(result.documents) > 1)
            self.assertEqual(
                result.documents[0].metadata['mime_type'],
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.docx')

    def test_process_pptx(self):
        with open(f'{self.fixtures_dir}/sample.pptx', 'rb') as file_p:
            file_data = file_p.read()
            mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            result = LocalTextExtractorProcessor().process(
                input=TextExtractorInput(
                    data=file_data, mime_type=mime_type, id='sample.pptx'),
                configuration=None
            )
            self.assertEqual(len(result.documents), 1)
            self.assertEqual(result.documents[0].content, 'Title\nSubtitle')
            self.assertEqual(
                result.documents[0].metadata['mime_type'],
                'application/vnd.openxmlformats-officedocument.presentationml.presentation')
            self.assertEqual(
                result.documents[0].metadata['file_name'], 'sample.pptx')


if __name__ == '__main__':
    unittest.main()
