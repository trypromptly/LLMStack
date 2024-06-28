from typing import Dict, Optional

import boto3

from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.source import (
    DataSourceConfigurationSchema,
    DataSourceInputSchema,
    DataSourceOutputSchema,
)


class S3PathInput(DataSourceInputSchema):
    path: str
    bucket: str


class S3PathConfiguration(DataSourceConfigurationSchema):
    region_name: Optional[str] = None
    api_version: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    config: Optional[Dict] = None


class S3Path(
    ProcessorInterface[
        S3PathInput,
        DataSourceOutputSchema,
        S3PathConfiguration,
    ],
):
    def _get_file_content(self, s3_object_get_response):
        content = s3_object_get_response["Body"].read()
        if isinstance(content, bytes):
            return content
        elif isinstance(content, str):
            return content.encode("utf-8")
        else:
            raise Exception("Unknown content type")

    def process(
        self,
        input: S3PathInput,
        configuration: S3PathConfiguration,
    ) -> DataSourceOutputSchema:
        s3_client = boto3.client("s3", **configuration.model_dump())
        data = s3_client.get_object(Bucket=input.bucket, Key=input.path)
        content = data["Body"].read()
        request_metadata = data["ResponseMetadata"]

        return DataSourceOutputSchema(
            documents=[
                DataDocument(
                    content=(
                        content
                        if isinstance(
                            content,
                            bytes,
                        )
                        else content.encode("utf-8")
                    ),
                    context_text=(
                        content
                        if isinstance(
                            content,
                            str,
                        )
                        else content.decode("utf-8")
                    ),
                    metadata={
                        "file_name": f"{input.bucket}/{input.path}",
                        **request_metadata,
                    },
                ),
            ],
        )
