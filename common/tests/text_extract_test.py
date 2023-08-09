import base64
import os
import unittest

from common.utils.text_extract import extract_text_from_b64_json
from common.utils.text_extract import extract_text_from_url
from common.utils.text_extract import ExtraParams


class TestDataURL(unittest.TestCase):
    def test_plain_extract_text_from_b64_json(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        with open(f'{dir}/fixtures/sample.txt', 'r') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data.encode('utf-8'))
            mime_type = 'text/plain'
            text = extract_text_from_b64_json(
                mime_type=mime_type, base64_encoded_data=base64_encoded_data, file_name='sample.txt', extra_params=None,
            )
            self.assertIn(
                'Aeque enim contingit omnibus fidibus, ut incontentae sint.', text,
            )

    def test_csv_extract_text_from_b64_json(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        with open(f'{dir}/fixtures/sample.csv', 'r') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data.encode('utf-8'))
            mime_type = 'text/csv'
            text = extract_text_from_b64_json(
                mime_type=mime_type, base64_encoded_data=base64_encoded_data, file_name='sample.csv', extra_params=None,
            )
            self.assertIn('Game Number", "Game Length', text)

    def test_mp3_extract_text_from_b64_json(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        with open(f'{dir}/fixtures/sample.mp3', 'rb') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data)
            mime_type = 'audio/mp3'
            text = extract_text_from_b64_json(
                mime_type=mime_type, base64_encoded_data=base64_encoded_data, file_name='sample.mp3', extra_params=ExtraParams(openai_key=os.environ['OPENAI_KEY']),
            )
            self.assertGreater(len(text), 0)

    def test_mp4_extract_text_from_b64_json(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        with open(f'{dir}/fixtures/sample.mp4', 'rb') as file_p:
            file_data = file_p.read()
            base64_encoded_data = base64.encodebytes(file_data)
            mime_type = 'video/mp4'
            text = extract_text_from_b64_json(
                mime_type=mime_type, base64_encoded_data=base64_encoded_data, file_name='sample.mp4', extra_params=ExtraParams(openai_key=os.environ['OPENAI_KEY']),
            )
            self.assertGreater(len(text), 0)


class TestHttpURL(unittest.TestCase):
    def test_html_extract_text_from_url(self):

        text = extract_text_from_url(
            url='http://example.com',
        )
        self.assertGreater(len(text), 0)

    def test_pdf_extract_text_from_url(self):

        text = extract_text_from_url(
            url='https://arxiv.org/pdf/2303.16183.pdf',
        )
        self.assertGreater(len(text), 0)

    def test_docx_extract_text_from_url(self):

        text = extract_text_from_url(
            url='https://file-examples.com/storage/fe0d875dfd645260e96b346/2017/02/file-sample_100kB.docx',
        )
        self.assertGreater(len(text), 0)

    def test_rtf_extract_text_from_url(self):
        text = extract_text_from_url(
            url='https://file-examples.com/storage/fe0d875dfd645260e96b346/2019/09/file-sample_100kB.rtf',
        )
        self.assertGreater(len(text), 0)


if __name__ == '__main__':
    unittest.main()
