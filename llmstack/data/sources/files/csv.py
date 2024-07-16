import logging

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource

logger = logging.getLogger(__name__)


class CSVFileSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={
            "widget": "file",
            "accept": {
                "text/csv": [],
            },
            "maxSize": 20000000,
        },
    )

    @classmethod
    def slug(cls):
        return "csv"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def display_name(self):
        mime_type, file_name, file_data = validate_parse_data_uri(self.file)
        return file_name

    def get_data_documents(self):
        mime_type, file_name, file_data = validate_parse_data_uri(self.file)
        if mime_type != "text/csv":
            raise ValueError(f"Invalid mime type: {mime_type}, expected: text/csv")

        data_uri = f"data:{mime_type};name={file_name};base64,{file_data}"

        result = Uri().process(
            input=UriInput(
                env=DataSourceEnvironmentSchema(
                    openai_key=self.openai_key,
                ),
                uri=data_uri,
            ),
            configuration=UriConfiguration(),
        )
        file_text = ""
        for doc in result.documents:
            file_text += doc.content.decode() + "\n"

        docs = [
            Document(page_content_key=self.get_content_key(), page_content=t, metadata={"source": file_name})
            for t in CSVTextSplitter(
                chunk_size=2, length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken
            ).split_text(file_text)
        ]

        return docs