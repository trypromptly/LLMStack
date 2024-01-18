import base64
import io
import logging
import zipfile
from typing import List, Optional

import magic
from pydantic import Field

from llmstack.base.models import Profile
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.datasources.handlers.datasource_processor import (
    WEAVIATE_SCHEMA,
    DataSourceEntryItem,
    DataSourceProcessor,
    DataSourceSchema,
)
from llmstack.datasources.handlers.utils import extract_documents
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)


class NotionExportSchema(DataSourceSchema):
    file: str = Field(
        ...,
        widget="file",
        description="File to be processed",
        accepts={
            "application/zip": [],
        },
        maxSize=10000000,
    )

    @staticmethod
    def get_content_key() -> str:
        return "content"

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=NotionExportSchema.get_content_key(),
        )


class NotionExportDataSource(DataSourceProcessor[NotionExportSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key("openai_key")

    @staticmethod
    def name() -> str:
        return "notion_export"

    @staticmethod
    def slug() -> str:
        return "notion_export"

    @staticmethod
    def description() -> str:
        return "Notion export"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = NotionExportSchema(**data)
        mime_type, file_name, file_data = validate_parse_data_uri(entry.file)
        zip_file_object = io.BytesIO(base64.b64decode(file_data))
        result = []
        with zipfile.ZipFile(zip_file_object, "r") as zip_ref:
            for file_name in zip_ref.namelist():
                mime = magic.Magic(mime=True)

                file_content = zip_ref.read(file_name)
                mime_type = mime.from_buffer(file_content)
                data_source_entry = DataSourceEntryItem(
                    name=file_name,
                    data={
                        "mime_type": mime_type,
                        "file_name": file_name,
                        "file_data": file_content,
                    },
                )
                result.append(data_source_entry)

        return result

    def get_data_documents(
        self,
        data: DataSourceEntryItem,
    ) -> Optional[DataSourceEntryItem]:
        docs = extract_documents(
            file_data=data.data["file_data"],
            content_key=NotionExportSchema.get_content_key(),
            mime_type=data.data["mime_type"],
            file_name=data.data["file_name"],
            metadata={"source": data.data["file_name"]},
        )

        return docs
