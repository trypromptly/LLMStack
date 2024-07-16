import base64
import logging
from io import BytesIO

from pydantic import Field
from unstructured.documents.elements import PageBreak
from unstructured.partition.pdf import partition_pdf

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource

DATA_URL_REGEX = r"data:application\/(\w+);name=(.*);base64,(.*)"


logger = logging.getLogger(__name__)


class PdfSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={
            "widget": "file",
            "accepts": {
                "application/pdf": [],
            },
            "maxSize": 20000000,
        },
    )

    @classmethod
    def slug(cls):
        return "pdf"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def display_name(self):
        mime_type, file_name, file_data = validate_parse_data_uri(self.file)
        return file_name

    def get_documents(self):
        mime_type, file_name, file_data = validate_parse_data_uri(self.file)
        decoded_data = base64.b64decode(file_data)
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
                                "source": f"file_{file_name}_page_{page_number}",
                                "page_number": page_number,
                                "file_name": file_name,
                            },
                        ),
                    )
                page_content = ""
            else:
                page_content += str(element)
                page_number = element.metadata.page_number
        return docs
