import re
from typing import Dict
from typing import Generator
from typing import Generic
from typing import List
from typing import Optional

import boto3

from common.promptly.blocks.data_extracter.aws_s3_path import AWSS3FileData
from common.promptly.blocks.data_extracter.aws_s3_path import AWSS3PathDataExtractorBlock
from common.promptly.core.base import BaseConfiguration
from common.promptly.core.base import BaseConfigurationType
from common.promptly.core.base import BaseInput
from common.promptly.core.base import BaseInputType
from common.promptly.core.base import BaseOutput
from common.promptly.core.base import BaseOutputType
from common.promptly.core.base import BaseProcessor


class AWSS3BucketDataExtractorBlockInput(BaseInput):
    bucket: str
    regex: Optional[str] = None


class AWSS3BucketDataExtractorBlockOutput(BaseOutput):
    data: List[AWSS3FileData]


class AWSS3BucketDataExtractorBlockConfiguration(BaseConfiguration):
    region_name: Optional[str] = None
    api_version: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    config: Optional[Dict] = None


class AWSS3BucketDataExtractorBlock(BaseProcessor[AWSS3BucketDataExtractorBlockInput, AWSS3BucketDataExtractorBlockOutput, AWSS3BucketDataExtractorBlockConfiguration],  Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    def __init__(self, configuration: dict):
        super().__init__(configuration)
        self._s3_client = boto3.client('s3', **configuration)
        self._s3_file_data_extractor = AWSS3PathDataExtractorBlock(
            configuration=configuration,
        )

    def _process(self, input: AWSS3BucketDataExtractorBlockInput, configuration: AWSS3BucketDataExtractorBlockConfiguration) -> AWSS3BucketDataExtractorBlockOutput:
        result = []
        try:
            input_regex = re.compile(input.regex) if input.regex else None
        except Exception:
            input_regex = None

        for file in self._s3_client.list_objects_v2(Bucket=input.bucket)['Contents']:
            if input_regex and not input_regex.match(file['Key']):
                continue
            file_response = self._s3_file_data_extractor.process(
                {'path': file['Key'], 'bucket': input.bucket},
            )
            result.append(file_response.result)
        return AWSS3BucketDataExtractorBlockOutput(data=result)

    def _process_iter(self, input: AWSS3BucketDataExtractorBlockInput, configuration: AWSS3BucketDataExtractorBlockConfiguration) -> Generator[AWSS3BucketDataExtractorBlockOutput, None, None]:
        try:
            input_regex = re.compile(input.regex) if input.regex else None
        except Exception:
            input_regex = None

        # Walk through files in bucket matching regex
        for file in self._s3_client.list_objects_v2(Bucket=input.bucket)['Contents']:
            if input_regex and not input_regex.match(file['Key']):
                continue

            for file_response in self._s3_file_data_extractor.process_iter({'path': file['Key'], 'bucket': input.bucket}):
                yield AWSS3BucketDataExtractorBlockOutput(data=[file_response.result])
