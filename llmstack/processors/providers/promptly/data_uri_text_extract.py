import concurrent.futures
import logging
import time
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import conint
from pydantic import Field

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.blocks.data.store.vectorstore.temp_weaviate import TempWeaviate
from llmstack.common.utils.text_extract import extract_text_from_b64_json, ExtraParams
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class DataUriTextExtractorConfiguration(ApiProcessorSchema):
    document_limit: Optional[conint(ge=0, le=10)] = Field(
        description='The maximum number of documents to return', default=1, advanced_parameter=True,
    )
    text_chunk_size: Optional[conint(ge=500, le=2000)] = Field(
        description='Chunksize of document', default=1500, advanced_parameter=True,
    )


class DataUriTextExtractorInput(ApiProcessorSchema):
    file: str = Field(
        default='', description='The file to extract text from', accepts={
            'application/pdf': [],
            'application/rtf': [],
            'text/plain': [],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [],
            'application/msword': [],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': [],
            'application/vnd.ms-powerpoint': [],
            'image/jpeg': [], 'image/png': [],
        }, maxSize=50000000, widget='file',
    )
    file_data: Optional[str] = Field(
        default='', description='The base64 encoded data of file', pattern=r'data:(.*);name=(.*);base64,(.*)',
    )
    query: Optional[str] = Field(
        default='', description='The query to search the document',
    )


class DataUriTextExtractorOutput(ApiProcessorSchema):
    text: str = Field(
        default='', description='The extracted text from the file', widget='textarea',
    )


class DataUriTextExtract(ApiProcessorInterface[DataUriTextExtractorInput, DataUriTextExtractorOutput, DataUriTextExtractorConfiguration]):
    """
    DataUri Text Extractor processor
    """

    def process_session_data(self, session_data):
        self.file_name = session_data['file_name'] if 'file_name' in session_data else ''
        self.mime_type = session_data['mime_type'] if 'mime_type' in session_data else ''
        self.data = session_data['data'] if 'data' in session_data else ''
        self.extracted_text = session_data['extracted_text'] if 'extracted_text' in session_data else ''
        self.storage_index_name = session_data['storage_index_name'] if 'storage_index_name' in session_data else ''

    @staticmethod
    def name() -> str:
        return 'File Extractor'

    @staticmethod
    def slug() -> str:
        return 'data_uri_text_extract'

    @staticmethod
    def description() -> str:
        return 'Extract text from file represened as data uri'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def session_data_to_persist(self) -> dict:
        return {
            'extracted_text': self.extracted_text,
            'storage_index_name': self.storage_index_name,
            'file_name': self.file_name,
            'mime_type': self.mime_type,
            'data': self.data,
        }

    def process(self) -> str:
        openai_api_key = self._env.get('openai_api_key', None)
        weaviate_url = self._env['weaviate_url']
        weaviate_api_key = self._env.get('weaviate_api_key', None)
        azure_openai_api_key = self._env.get('azure_openai_api_key', None)
        weaviate_embedding_endpoint = self._env['weaviate_embedding_endpoint']
        weaviate_text2vec_config = self._env['weaviate_text2vec_config']

        query = self._input.query

        self.temp_store = TempWeaviate(
            url=weaviate_url,
            openai_key=openai_api_key,
            azure_openai_key=azure_openai_api_key,
            weaviate_rw_api_key=weaviate_api_key,
            weaviate_embedding_endpoint=weaviate_embedding_endpoint,
            weaviate_text2vec_config=weaviate_text2vec_config,
        )

        file = self._input.file or None
        if (file is None or file == '') and self._input.file_data:
            file = self._input.file_data

        if file is None:
            raise Exception('No file found in input')
        mime_type, file_name, data = validate_parse_data_uri(file)

        if (query is None or query == '') and mime_type == self.mime_type and file_name == self.file_name and data == self.data and self.extracted_text != '':
            async_to_sync(self._output_stream.write)(
                DataUriTextExtractorOutput(text=self.extracted_text),
            )
            output = self._output_stream.finalize()
            return output

        if query and self.storage_index_name:
            documents: List[Document] = self.temp_store.search_temp_index(
                self.storage_index_name, query, self._config.document_limit,
            )

            async_to_sync(self._output_stream.write)(
                DataUriTextExtractorOutput(text='\n'.join(
                    [document.page_content for document in documents])),
            )
            output = self._output_stream.finalize()
            return output

        self.mime_type = mime_type
        self.file_name = file_name
        self.data = data

        text = extract_text_from_b64_json(
            mime_type=mime_type, base64_encoded_data=data,
            file_name=file_name,
            extra_params=ExtraParams(openai_key=openai_api_key),
        )
        self.extracted_text = text

        if query:
            index_name = self.temp_store.create_temp_index()
            self.storage_index_name = index_name
            with concurrent.futures.ThreadPoolExecutor() as executor:
                text_chunks = SpacyTextSplitter(
                    separator='\n', pipeline='sentencizer', chunk_size=self._config.text_chunk_size,
                ).split_text(text)
                futures = [
                    executor.submit(
                        self.temp_store.add_content,
                        index_name, text_chunk, source=file_name,
                    ) for text_chunk in text_chunks
                ]
                concurrent.futures.wait(futures)
            documents: List[Document] = self.temp_store.search_temp_index(
                self.storage_index_name, query, self._config.document_limit,
            )

            async_to_sync(self._output_stream.write)(
                DataUriTextExtractorOutput(text='\n'.join(
                    [document.page_content for document in documents])),
            )
            output = self._output_stream.finalize()
            return output

        async_to_sync(self._output_stream.write)(
            DataUriTextExtractorOutput(text=text),
        )
        output = self._output_stream.finalize()
        return output
