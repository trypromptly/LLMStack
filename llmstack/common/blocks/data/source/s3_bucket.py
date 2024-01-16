import re
from typing import Dict, Optional

import boto3

from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.source import (DataSourceConfigurationSchema,
                                                DataSourceInputSchema,
                                                DataSourceOutputSchema)


class S3BucketInput(DataSourceInputSchema):
    regex: Optional[str] = None
    bucket: str


class S3BucketConfiguration(DataSourceConfigurationSchema):
    region_name: Optional[str] = None
    api_version: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    config: Optional[Dict] = None


class S3Bucket(
    ProcessorInterface[
        S3BucketInput,
        DataSourceOutputSchema,
        S3BucketConfiguration,
    ],
):
    def process(
        self,
        input: S3BucketInput,
        configuration: S3BucketConfiguration,
    ) -> DataSourceOutputSchema:
        documents = []
        s3_client = boto3.client("s3", **configuration.dict())
        try:
            input_regex = re.compile(input.regex) if input.regex else None
        except Exception:
            input_regex = None

        for file in s3_client.list_objects_v2(Bucket=input.bucket)["Contents"]:
            if input_regex and not input_regex.match(file["Key"]):
                continue
            data = s3_client.get_object(Bucket=input.bucket, Key=file["Key"])
            content = data["Body"].read()
            request_metadata = data["ResponseMetadata"]
            documents.append(
                DataDocument(
                    content=content if isinstance(content, bytes) else None,
                    context_text=content if isinstance(content, str) else None,
                    metadata={
                        "file_name": f"{input.bucket}/{file['Key']}",
                        **request_metadata,
                    },
                ),
            )
        return DataSourceOutputSchema(documents=documents)
