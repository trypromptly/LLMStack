import unittest
import os

from llmstack.common.blocks.data.source.s3_path import S3Path, S3PathInput, S3PathConfiguration


class S3PathTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.region_name = os.environ.get('AWS_REGION_NAME')
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

    def test_process(self):
        result = S3Path().process(
            input=S3PathInput(
                bucket='makerdojotest',
                path='test_shopify.csv'
            ),
            configuration=S3PathConfiguration(
                region_name=self.region_name,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
        )
        self.assertTrue(len(result.documents) > 0)
        self.assertEqual(result.documents[0].metadata.get(
            'file_name'), 'makerdojotest/test_shopify.csv')
        self.assertEqual(result.documents[0].metadata.get(
            'HTTPHeaders').get('content-type'), 'text/csv')


if __name__ == '__main__':
    unittest.main()
