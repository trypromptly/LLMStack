import logging
from typing import List
from typing import Optional

from pydantic import Field

from common.blocks.data.store.vectorstore import Document
from common.utils.text_extract import extract_text_from_b64_json
from common.utils.text_extract import ExtraParams
from common.utils.splitter import SpacyTextSplitter
from common.utils.utils import validate_parse_data_uri
from datasources.handlers.datasource_type_interface import DataSourceEntryItem
from datasources.handlers.datasource_type_interface import DataSourceSchema
from datasources.handlers.datasource_type_interface import DataSourceProcessor
from datasources.handlers.datasource_type_interface import WEAVIATE_SCHEMA

logger = logging.getLogger(__name__)


class MediaFileSchema(DataSourceSchema):
    file: str = Field(
        ..., widget='file',
        description='File to be processed', accepts={
            'audio/mpeg': [],
            'audio/mp3': [],
            'video/mp4': [],
            'video/webm': [],
        }, maxSize=20000000,
    )

    @staticmethod
    def get_content_key() -> str:
        return 'content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=MediaFileSchema.get_content_key(),
        )


class MediaFileDataSource(DataSourceProcessor[MediaFileSchema]):
    @staticmethod
    def name() -> str:
        return 'media_file'

    @staticmethod
    def slug() -> str:
        return 'media_file'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = MediaFileSchema(**data)
        mime_type, file_name, file_data = validate_parse_data_uri(entry.file)

        if mime_type not in ['audio/mpeg', 'audio/mp3', 'video/mp4', 'video/webm']:
            raise ValueError(
                f'Invalid mime type: {mime_type}, expected: audio/mpeg or audio/mp3 or video/mp4 or video/webm',
            )

        data_source_entry = DataSourceEntryItem(
            name=file_name, data={'mime_type': mime_type,
                                  'file_name': file_name, 'file_data': file_data},
        )

        return [data_source_entry]

    def get_data_documents(self, data: DataSourceEntryItem) -> Optional[DataSourceEntryItem]:
        openai_key = self.profile.get_vendor_key('openai_key')

        logger.info(
            f"Processing file: {data.data['file_name']} mime_type: {data.data['mime_type']}",
        )

        file_text = extract_text_from_b64_json(
            mime_type=data.data['mime_type'],
            base64_encoded_data=data.data['file_data'], 
            file_name=data.data['file_name'], extra_params=ExtraParams(
                openai_key=openai_key),
        )

        docs = [
            Document(
                page_content_key=self.get_content_key(),
                page_content=t,
                metadata={'source': data.data['file_name']},
            ) for t in SpacyTextSplitter(chunk_size=1500).split_text(file_text)
        ]

        return docs

    def similarity_search(self, query: str, *args, **kwargs) -> List[dict]:
        return super().similarity_search(query, *args, **kwargs)
