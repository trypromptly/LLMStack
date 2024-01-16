import logging
from typing import List, Optional

from pydantic import Field

from llmstack.base.models import Profile
from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import (Uri, UriConfiguration,
                                                    UriInput)
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.datasources.handlers.datasource_processor import (
    WEAVIATE_SCHEMA, DataSourceEntryItem, DataSourceProcessor,
    DataSourceSchema)
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)


class FileSchema(DataSourceSchema):
    file: str = Field(
        ...,
        widget="file",
        description="File to be processed",
        accepts={
            "application/pdf": [],
            "application/json": [],
            "audio/mpeg": [],
            "application/rtf": [],
            "text/plain": [],
            "text/csv": [],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": [],
            "audio/mp3": [],
            "video/mp4": [],
            "video/webm": [],
        },
        maxSize=25000000,
        maxFiles=4,
    )

    @staticmethod
    def get_content_key() -> str:
        return "content"

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=FileSchema.get_content_key(),
        )


class FileDataSource(DataSourceProcessor[FileSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key("openai_key")

    @staticmethod
    def name() -> str:
        return "file"

    @staticmethod
    def slug() -> str:
        return "file"

    @staticmethod
    def description() -> str:
        return "File"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = FileSchema(**data)
        files = entry.file.split("|")
        data_source_entries = []
        for file in files:
            mime_type, file_name, file_data = validate_parse_data_uri(file)

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

    def get_data_documents(
        self,
        data: DataSourceEntryItem,
    ) -> Optional[DataSourceEntryItem]:
        logger.info(
            f"Processing file: {data.data['file_name']} mime_type: {data.data['mime_type']}",
        )
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

        if data.data["mime_type"] == "text/csv":
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
