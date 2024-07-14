import logging
from typing import List, Optional

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.datasource_processor import (
    DataPipeline,
    DataSourceEntryItem,
    DataSourceSchema,
)

logger = logging.getLogger(__name__)


class CSVFileSchema(DataSourceSchema):
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

    @staticmethod
    def get_content_key() -> str:
        return "content"


class CSVFileDataSource(DataPipeline[CSVFileSchema]):
    @staticmethod
    def name() -> str:
        return "csv_file"

    @staticmethod
    def slug() -> str:
        return "csv_file"

    @staticmethod
    def description() -> str:
        return "CSV file"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = CSVFileSchema(**data)
        mime_type, file_name, file_data = validate_parse_data_uri(entry.file)
        if mime_type != "text/csv":
            raise ValueError(
                f"Invalid mime type: {mime_type}, expected: text/csv",
            )

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
        data_uri = f"data:{data.data['mime_type']};name={data.data['file_name']};base64,{data.data['file_data']}"

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
            Document(
                page_content_key=self.get_content_key(),
                page_content=t,
                metadata={
                    "source": data.data["file_name"],
                },
            )
            for t in CSVTextSplitter(
                chunk_size=2,
                length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
            ).split_text(file_text)
        ]

        return docs
