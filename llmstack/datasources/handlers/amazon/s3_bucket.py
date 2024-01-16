import base64
import logging
from enum import Enum
from typing import List, Optional

from pydantic import Field, SecretStr

from llmstack.base.models import Profile
from llmstack.common.blocks.data.source.s3_bucket import (
    S3Bucket, S3BucketConfiguration, S3BucketInput)
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.common.utils.text_extract import (ExtraParams,
                                                extract_text_from_b64_json)
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.datasources.handlers.datasource_processor import (
    WEAVIATE_SCHEMA, DataSourceEntryItem, DataSourceProcessor,
    DataSourceSchema)
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)


class MimeType(str, Enum):
    PLAIN_TEXT = "text/plain"
    CSV = "text/csv"
    JSON = "application/json"
    PDF = "application/pdf"
    RTF = "application/rtf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    HTML = "text/html"
    MP3 = "audio/mpeg"
    MP4 = "video/mp4"
    WEBM = "video/webm"

    def __str__(self):
        return self.value


class S3BucketSchema(DataSourceSchema):
    bucket: str = Field(description="S3 bucket name")
    regex: Optional[str] = Field(description="Regex to filter files")
    mime_type: Optional[MimeType] = Field(
        default=MimeType.CSV,
        description="Mime type of the files",
    )
    aws_access_key_id: Optional[str] = Field(
        description="AWS access key ID",
        default=None,
    )
    aws_secret_access_key: Optional[SecretStr] = Field(
        description="AWS secret access key",
        widget="password",
    )
    split_csv: Optional[bool] = Field(
        default=False,
        description="Split CSV file",
    )
    region_name: Optional[str] = Field(
        description="AWS region name",
        default="us-east-1",
    )

    @staticmethod
    def get_content_key() -> str:
        return "content"

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=S3BucketSchema.get_content_key(),
        )


class S3BucketDataSource(DataSourceProcessor[S3BucketSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.profile = profile
        self.openai_key = profile.get_vendor_key("openai_key")
        self.split_csv = None

    @staticmethod
    def name() -> str:
        return "s3 bucket"

    @staticmethod
    def slug() -> str:
        return "s3_bucket"

    @staticmethod
    def description() -> str:
        return "Reads files from an S3 bucket"

    @staticmethod
    def provider_slug() -> str:
        return "amazon"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = S3BucketSchema(**data)
        mime_type = entry.mime_type
        self.split_csv = entry.split_csv

        bucket_name = entry.bucket
        if entry.aws_access_key_id:
            aws_access_key_id = entry.aws_access_key_id
        else:
            aws_access_key_id = self.profile.get_vendor_key(
                "aws_access_key_id",
            )

        if entry.aws_secret_access_key:
            aws_secret_access_key_secret = (
                entry.aws_secret_access_key.get_secret_value() if entry.aws_secret_access_key else None
            )
        else:
            aws_secret_access_key_secret = self.profile.get_vendor_key(
                "aws_secret_access_key",
            )

        if entry.region_name:
            region_name = entry.region_name
        else:
            region_name = self.profile.get_vendor_key("aws_default_region")

        result = S3Bucket().process(
            input=S3BucketInput(bucket=bucket_name, regex=entry.regex),
            configuration=S3BucketConfiguration(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key_secret,
                region_name=region_name,
            ),
        )

        data_source_entries = []

        for document in result.documents:
            file_name = document.metadata["file_name"]
            base64_encoded_file_content = base64.b64encode(
                document.content,
            ).decode()
            data_url = "data:{};name={};base64,{}".format(
                mime_type,
                file_name,
                base64_encoded_file_content,
            )
            mime_type, file_name, file_data = validate_parse_data_uri(data_url)
            data_source_entry = DataSourceEntryItem(
                name=file_name,
                data={
                    "mime_type": mime_type,
                    "file_name": file_name,
                    "file_data": file_data,
                },
            )
            data_source_entries.append(data_source_entry)

        return data_source_entries

    def get_data_documents(self, data: dict) -> Optional[DataSourceEntryItem]:
        logger.info(
            f"Processing file: {data.data['file_name']} mime_type: {data.data['mime_type']}",
        )

        file_text = extract_text_from_b64_json(
            data.data["mime_type"],
            data.data["file_data"],
            file_name=data.data["file_name"],
            extra_params=ExtraParams(
                openai_key=self.openai_key,
            ),
        )

        if data.data["mime_type"] == "text/csv":
            docs = []
            for entry in CSVTextSplitter(
                chunk_size=2,
                length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
            ).split_text(file_text):
                if self.split_csv:
                    for entry_chunk in SpacyTextSplitter(
                        chunk_size=1500,
                    ).split_text(file_text):
                        docs.append(
                            Document(
                                page_content_key=self.get_content_key(),
                                page_content=entry_chunk,
                                metadata={
                                    "source": data.data["file_name"],
                                },
                            ),
                        )
                else:
                    docs.append(
                        Document(
                            page_content_key=self.get_content_key(),
                            page_content=entry,
                            metadata={
                                "source": data.data["file_name"],
                            },
                        ),
                    )

        else:
            docs = [
                Document(
                    page_content_key=self.get_content_key(),
                    page_content=t,
                    metadata={
                        "source": data.data["file_name"],
                    },
                )
                for t in SpacyTextSplitter(
                    chunk_size=1500,
                ).split_text(file_text)
            ]

        return docs
