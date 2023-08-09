from datetime import datetime
from typing import Dict
from typing import Generator
from typing import Generic
from typing import Optional

import boto3

from common.promptly.core.base import BaseConfiguration
from common.promptly.core.base import BaseConfigurationType
from common.promptly.core.base import BaseInput
from common.promptly.core.base import BaseInputType
from common.promptly.core.base import BaseOutput
from common.promptly.core.base import BaseOutputType
from common.promptly.core.base import BaseProcessor
from common.promptly.core.base import Schema


class AWSS3PathDataExtractorBlockInput(BaseInput):
    """ S3 file path to extract data from"""
    path: str
    bucket: str


class S3ResponseMetadata(Schema):
    host_id: str
    http_headers: Dict[str, str]
    http_status_code: int
    request_id: str
    retry_attempts: int
    accepted_ranges: Optional[str] = None
    last_modified: Optional[datetime] = None
    content_length: Optional[int] = None
    etag: Optional[str] = None
    content_type: Optional[str] = None
    server_side_encryption: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class AWSS3FileData(Schema):
    metadata: S3ResponseMetadata
    content: bytes
    path: str


class AWSS3PathDataExtractorBlockOutput(BaseOutput):
    result: AWSS3FileData


class AWSS3PathDataExtractorBlockConfiguration(BaseConfiguration):
    region_name: Optional[str] = None
    api_version: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    config: Optional[Dict] = None


class AWSS3PathDataExtractorBlock(BaseProcessor[AWSS3PathDataExtractorBlockInput, AWSS3PathDataExtractorBlockOutput, AWSS3PathDataExtractorBlockConfiguration],  Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    def __init__(self, configuration: dict):
        super().__init__(configuration)
        self._s3_client = boto3.client('s3', **configuration)

    def _get_metadata(self, s3_object_get_response):
        request_metadata = s3_object_get_response['ResponseMetadata']
        return S3ResponseMetadata(
            request_id=request_metadata['RequestId'],
            host_id=request_metadata['HostId'],
            http_headers=request_metadata['HTTPHeaders'],
            http_status_code=request_metadata['HTTPStatusCode'],
            retry_attempts=request_metadata['RetryAttempts'],
            accepted_ranges=s3_object_get_response.get(
                'AcceptRanges',
            ),
            last_modified=s3_object_get_response.get(
                'LastModified',
            ),
            content_length=s3_object_get_response.get(
                'ContentLength',
            ),
            etag=s3_object_get_response.get('ETag'),
            content_type=s3_object_get_response.get(
                'ContentType',
            ),
            server_side_encryption=s3_object_get_response.get(
                'ServerSideEncryption',
            ),
            metadata=s3_object_get_response.get(
                'Metadata',
            ),
        )

    def _get_file_content(self, s3_object_get_response):
        content = s3_object_get_response['Body'].read()
        if type(content) == bytes:
            return content
        elif type(content) == str:
            return content.encode('utf-8')
        else:
            raise Exception('Unknown content type')

    def _process(self, input: AWSS3PathDataExtractorBlockInput, configuration: AWSS3PathDataExtractorBlockConfiguration) -> AWSS3PathDataExtractorBlockOutput:
        data = self._s3_client.get_object(Bucket=input.bucket, Key=input.path)

        return AWSS3PathDataExtractorBlockOutput(
            result=AWSS3FileData(
                metadata=self._get_metadata(data),
                content=self._get_file_content(
                    data,
                ),
                path=f'{input.bucket}/{input.path}',
            ),
        )

    def _process_iter(self, input: AWSS3PathDataExtractorBlockInput, configuration: AWSS3PathDataExtractorBlockConfiguration) -> Generator[AWSS3PathDataExtractorBlockOutput, None, None]:
        # Read file byte by byte
        data = self._s3_client.get_object(Bucket=input.bucket, Key=input.path)
        for line in data['Body']:
            yield AWSS3PathDataExtractorBlockOutput(
                result=AWSS3FileData(
                metadata=self._get_metadata(data),
                content=line,
                path=f'{input.bucket}/{input.path}',
                ),
            )
