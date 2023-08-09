import logging
from typing import List

from common.promptly.vectorstore import Document
from common.utils.splitter import SpacyTextSplitter
from datasources.handlers.datasource_type_interface import DataSourceEntryItem
from datasources.handlers.datasource_type_interface import DataSourceSchema
from datasources.handlers.datasource_type_interface import DataSourceTypeInterface
from datasources.handlers.datasource_type_interface import WEAVIATE_SCHEMA

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


class TextDataSource(DataSourceTypeInterface[TextSchema]):

    @staticmethod
    def name() -> str:
        return 'text'

    @staticmethod
    def slug() -> str:
        return 'text'

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

    def similarity_search(self, query: str, *args, **kwargs) -> List[dict]:
        return super().similarity_search(query, *args, **kwargs)
