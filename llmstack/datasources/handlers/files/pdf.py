import base64
import logging
from io import BytesIO
from typing import List, Optional

from pydantic import AnyUrl, Field
from unstructured.documents.elements import PageBreak
from unstructured.partition.pdf import partition_pdf

from llmstack.base.models import Profile
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.datasources.handlers.datasource_processor import (
    WEAVIATE_SCHEMA,
    DataSourceEntryItem,
    DataSourceProcessor,
    DataSourceSchema,
)
from llmstack.datasources.models import DataSource

DATA_URL_REGEX = r"data:application\/(\w+);name=(.*);base64,(.*)"


logger = logging.getLogger(__name__)


class DataUrl(AnyUrl):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            {
                "format": "data-url",
                "pattern": r"data:(.*);name=(.*);base64,(.*)",
            },
        )


class PdfSchema(DataSourceSchema):
    file: str = Field(
        ...,
        widget="file",
        description="File to be processed",
        accepts={
            "application/pdf": [],
        },
        maxSize=20000000,
    )

    @staticmethod
    def get_content_key() -> str:
        return "content"

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=PdfSchema.get_content_key(),
        )


class PDFDataSource(DataSourceProcessor[PdfSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key("openai_key")

    @staticmethod
    def name() -> str:
        return "pdf"

    @staticmethod
    def slug() -> str:
        return "pdf"

    @staticmethod
    def description() -> str:
        return "PDF file"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = PdfSchema(**data)
        mime_type, file_name, file_data = validate_parse_data_uri(entry.file)

        data_source_entry = DataSourceEntryItem(
            name=file_name,
            data={
                "mime_type": mime_type,
                "file_name": file_name,
                "file_data": file_data,
            },
        )

        return [data_source_entry]

    def get_data_documents(
        self,
        data: DataSourceEntryItem,
    ) -> Optional[DataSourceEntryItem]:
        logger.info(
            f"Processing file: {data.data['file_name']} mime_type: {data.data['mime_type']}",
        )

        decoded_data = base64.b64decode(data.data["file_data"])
        data_fp = BytesIO(decoded_data)
        page_content = ""
        page_number = 0
        docs = []
        for element in partition_pdf(file=data_fp, include_page_breaks=True):
            if isinstance(element, PageBreak):
                page_content += "\n\n"
                for text_chunk in SpacyTextSplitter(
                    chunk_size=1500,
                ).split_text(page_content):
                    docs.append(
                        Document(
                            page_content_key=self.get_content_key(),
                            page_content=text_chunk,
                            metadata={
                                "source": f"file_{data.data['file_name']}_page_{page_number}",
                                "page_number": page_number,
                                "file_name": data.data["file_name"],
                            },
                        ),
                    )
                page_content = ""
            else:
                page_content += str(element)
                page_number = element.metadata.page_number
        return docs
