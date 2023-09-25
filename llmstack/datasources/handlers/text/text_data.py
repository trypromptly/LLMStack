import logging
from typing import List

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.datasources.handlers.datasource_type_interface import DataSourceEntryItem, DataSourceSchema, DataSourceProcessor, WEAVIATE_SCHEMA

logger = logging.getLogger(__file__)

"""
Entry configuration schema for text data source type
"""


class TextSchema(DataSourceSchema):
    name: str = 'Untitled'
    content: str = ''

    @staticmethod
    def get_content_key() -> str:
        return 'content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=TextSchema.get_content_key(),
        )


class TextDataSource(DataSourceProcessor[TextSchema]):

    @staticmethod
    def name() -> str:
        return 'text'

    @staticmethod
    def slug() -> str:
        return 'text'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = TextSchema(**data)
        data_source_entry = DataSourceEntryItem(
            name=entry.name, data=data,
        )
        return [data_source_entry]

    def get_data_documents(self, data: DataSourceEntryItem) -> DataSourceEntryItem:
        entry = TextSchema(**data.data)

        data_source_entry = DataSourceEntryItem(
            name=entry.name, config={}, size=0,
        )

        docs = [
            Document(page_content_key=self.get_content_key(), page_content=t, metadata={'source': entry.name}) for t in SpacyTextSplitter(
                chunk_size=1500,
            ).split_text(entry.content)
        ]

        return docs
