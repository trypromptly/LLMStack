import unittest 
import os

from common.blocks.data.text_extractor.whisper import WhisperTextExtractorProcessor, WhisperTextExtractorInput

class WhisperTextExtractorProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures_dir = __file__.replace('test_whisper.py', '../../../fixtures')

        self.api_key = os.environ.get('OPENAI_API_KEY')
    
    def test_process_mp3(self):
        with open(f'{self.fixtures_dir}/sample.mp3', 'rb') as file_p:
            file_data = file_p.read()
            mime_type = 'audio/mp3'
            result = WhisperTextExtractorProcessor().process(
                input=WhisperTextExtractorInput(data=file_data, 
                                          mime_type=mime_type, 
                                          id="sample.mp3",
                                          openai_api_key=self.api_key),
                configuration=None)
            self.assertTrue(len(result.documents) > 0)
            self.assertEqual(result.documents[0].metadata['file_name'], 'sample.mp3')
            self.assertEqual(result.documents[0].metadata['mime_type'], 'audio/mp3')
            
if __name__ == '__main__':
    unittest.main()