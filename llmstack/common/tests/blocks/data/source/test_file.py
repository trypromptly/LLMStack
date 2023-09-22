import unittest
from llmstack.common.blocks.data.source.file import File, FileInput, FileConfiguration


class FileTextLoaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures_dir = __file__.replace(
            'test_file.py', '../../../fixtures')

    def test_process(self):
        file_path = f'{self.fixtures_dir}/sample.txt'
        result = File().process(
            input=FileInput(file=file_path),
            configuration=FileConfiguration()
        )
        self.assertTrue(len(result.documents) > 0)
        self.assertEqual(
            result.documents[0].metadata['mime_type'], 'text/plain')
        self.assertEqual(
            result.documents[0].metadata['file_name'].split('/')[-1], 'sample.txt')


if __name__ == '__main__':
    unittest.main()
