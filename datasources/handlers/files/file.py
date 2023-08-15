import logging
from typing import List
from typing import Optional

from pydantic import Field

from common.blocks.data.store.vectorstore import Document
from common.utils.splitter import CSVTextSplitter
from common.utils.splitter import SpacyTextSplitter
from common.utils.utils import validate_parse_data_uri
from datasources.handlers.datasource_type_interface import DataSourceEntryItem
from datasources.handlers.datasource_type_interface import DataSourceSchema
from datasources.handlers.datasource_type_interface import DataSourceProcessor
from datasources.handlers.datasource_type_interface import WEAVIATE_SCHEMA
from datasources.models import DataSource
from base.models import Profile
from common.blocks.data.source.uri import Uri, UriInput, UriConfiguration
from common.blocks.data.source import DataSourceEnvironmentSchema


logger = logging.getLogger(__name__)


class FileSchema(DataSourceSchema):
    file: str = Field(
        ..., widget='file',
        description='File to be processed', accepts={
            'application/pdf': [],
            'application/json': [],
            'audio/mpeg': [],
            'application/rtf': [],
            'text/plain': [],
            'text/csv': [],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': [],
            'audio/mp3': [],
            'video/mp4': [],
            'video/webm': [],
        }, maxSize=250000000,
    )

    @staticmethod
    def get_content_key() -> str:
        return 'content'

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
        self.openai_key = profile.get_vendor_key('openai_key')

    @staticmethod
    def name() -> str:
        return 'file'

    @staticmethod
    def slug() -> str:
        return 'file'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = FileSchema(**data)
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
        data_uri = f"data:{data.data['mime_type']};name={data.data['file_name']};base64,{data.data['file_data']}"
        
        result = Uri().process(
            input=UriInput(env=DataSourceEnvironmentSchema(openai_key=self.openai_key), uri=data_uri), configuration=UriConfiguration()
        )
                
        file_text = ''
        for doc in result.documents:
            file_text += doc.content.decode() + '\n'
                
        
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

    def similarity_search(self, query: str, *args, **kwargs) -> List[dict]:
        return super().similarity_search(query, *args, **kwargs)
