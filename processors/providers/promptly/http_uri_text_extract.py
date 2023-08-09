import logging
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import conint
from pydantic import Field
from pydantic import HttpUrl

from common.promptly.vectorstore import Document
from common.promptly.vectorstore.temp_weaviate import TempWeaviate
from common.utils.text_extract import extract_text_from_url
from common.utils.text_extract import ExtraParams
from common.utils.splitter import SpacyTextSplitter
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import BaseSchema

logger = logging.getLogger(__name__)


class HttpUriTextExtractorConfiguration(BaseSchema):
    document_limit: Optional[conint(ge=0, le=10)] = Field(
        description='The maximum number of documents to return', default=1, advanced_parameter=True,
    )
    text_chunk_size: Optional[conint(ge=500, le=2000)] = Field(
        description='Chunksize of document', default=1500, advanced_parameter=True,
    )


class HttpUriTextExtractorInput(BaseSchema):
    url: str = Field(
        default='', description='The URL to extract text from', widget='text',
    )
    query: Optional[str] = Field(
        default='', description='The query to search the document',
    )


class HttpUriTextExtractorOutput(BaseSchema):
    text: str = Field(
        default='', description='The extracted text from the URL',
    )


class HttpUriTextExtract(ApiProcessorInterface[HttpUriTextExtractorInput, HttpUriTextExtractorOutput, HttpUriTextExtractorConfiguration]):
    """
    HttpUri Text Extractor processor
    """

    def process_session_data(self, session_data):
        self.url = session_data['url'] if 'url' in session_data else None
        self.extracted_text = session_data['extracted_text'] if 'extracted_text' in session_data else None
        self.storage_index_name = session_data['storage_index_name'] if 'storage_index_name' in session_data else None

    def slug() -> str:
        return 'promptly_http_uri_text_extract'

    def session_data_to_persist(self) -> dict:
        return {
            'url': self.url,
            'extracted_text': self.extracted_text,
        }

    def process(self) -> HttpUriTextExtractorOutput:
        openai_api_key = self._env.get('openai_api_key', None)
        weaviate_url = self._env['weaviate_url']
        weaviate_api_key = self._env.get('weaviate_api_key', None)
        azure_openai_api_key = self._env.get('azure_openai_api_key', None)
        weaviate_embedding_endpoint = self._env['weaviate_embedding_endpoint']
        weaviate_text2vec_config = self._env['weaviate_text2vec_config']

        query = self._input.query
        url = self._input.url.strip().rstrip()

        self.temp_store = TempWeaviate(
            url=weaviate_url,
            openai_key=openai_api_key,
            weaviate_rw_api_key=weaviate_api_key,
            azure_openai_key=azure_openai_api_key,
            weaviate_embedding_endpoint=weaviate_embedding_endpoint,
            weaviate_text2vec_config=weaviate_text2vec_config,
        )

        if (query is None or query == '') and url == self.url and self.extracted_text is not None:
            async_to_sync(self._output_stream.write)(
                HttpUriTextExtractorOutput(text=self.extracted_text),
            )
            output = self._output_stream.finalize()
            return output

        if query and self.storage_index_name and url == self.url:
            documents: List[Document] = self.temp_store.search_temp_index(
                self.storage_index_name, query, self._config.document_limit,
            )
            for document in documents:
                async_to_sync(self._output_stream.write)(
                    HttpUriTextExtractorOutput(text=document.page_content),
                )
                async_to_sync(self._output_stream.write)(
                    HttpUriTextExtractorOutput(text='\n'),
                )

            output = self._output_stream.finalize()
            return output

        text = extract_text_from_url(
            url, extra_params=ExtraParams(openai_key=openai_api_key),
        )
        self.extracted_text = text
        self.url = url

        if query:
            index_name = self.temp_store.create_temp_index()
            self.storage_index_name = index_name
            for text_chunk in SpacyTextSplitter(separator='\n', chunk_size=self._config.text_chunk_size).split_text(text):
                self.temp_store.add_content(
                    index_name, text_chunk, source=self.url,
                )
            documents: List[Document] = self.temp_store.search_temp_index(
                self.storage_index_name, query, self._config.document_limit,
            )

            for document in documents:
                async_to_sync(self._output_stream.write)(
                    HttpUriTextExtractorOutput(text=document.page_content),
                )
                async_to_sync(self._output_stream.write)(
                    HttpUriTextExtractorOutput(text='\n'),
                )

            output = self._output_stream.finalize()
            return output

        async_to_sync(self._output_stream.write)(
            HttpUriTextExtractorOutput(text=text),
        )
        output = self._output_stream.finalize()

        return output
