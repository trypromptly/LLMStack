import logging
from typing import List
from typing import Optional

from pydantic import Field

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter
from llmstack.common.utils.text_extract import extract_text_from_b64_json
from llmstack.common.utils.text_extract import ExtraParams
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.datasources.handlers.datasource_type_interface import DataSourceEntryItem, DataSourceSchema, DataSourceProcessor, WEAVIATE_SCHEMA
from llmstack.datasources.models import DataSource
from llmstack.base.models import Profile


logger = logging.getLogger(__name__)


class GdriveFileSchema(DataSourceSchema):
    file: str = Field(
        ..., widget='gdrive',
        description='File to be processed', accepts={
            'application/pdf': [],
            'application/json': [],
            'audio/mpeg': [],
            'application/rtf': [],
            'text/plain': [],
            'text/csv': [],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': [],
            'application/vnd.google-apps.presentation': [],
            'application/vnd.google-apps.document': [],
            'application/vnd.google-apps.spreadsheet': [],
            'audio/mp3': [],
            'video/mp4': [],
            'video/webm': [],
        }, maxSize=10000000,
    )

    @staticmethod
    def get_content_key() -> str:
        return 'content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=GdriveFileSchema.get_content_key(),
        )


class GdriveFileDataSource(DataSourceProcessor[GdriveFileSchema]):

    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key('openai_key')

    @staticmethod
    def name() -> str:
        return 'gdrive_file'

    @staticmethod
    def slug() -> str:
        return 'gdrive_file'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = GdriveFileSchema(**data)
        mime_type, file_name, file_data = validate_parse_data_uri(entry.file)

        data_source_entry = DataSourceEntryItem(
            name=file_name, data={'mime_type': mime_type,
                                  'file_name': file_name, 'file_data': file_data},
        )

        return [data_source_entry]

    def get_data_documents(self, data: DataSourceEntryItem) -> Optional[DataSourceEntryItem]:
        logger.info(
            f"Processing file: {data.data['file_name']} mime_type: {data.data['mime_type']}",
        )

        file_text = extract_text_from_b64_json(
            mime_type=data.data['mime_type'],
            base64_encoded_data=data.data['file_data'],
            file_name=data.data['file_name'],
            extra_params=ExtraParams(openai_key=self.openai_key),
        )

        if data.data['mime_type'] == 'text/csv':
            docs = [
                Document(page_content_key=self.get_content_key(), page_content=t, metadata={'source': data.data['file_name']}) for t in CSVTextSplitter(
                    chunk_size=2, length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
                ).split_text(file_text)
            ]
        else:
            docs = [
                Document(page_content_key=self.get_content_key(), page_content=t, metadata={'source': data.data['file_name']}) for t in SpacyTextSplitter(
                    chunk_size=1500,
                ).split_text(file_text)
            ]

        return docs
