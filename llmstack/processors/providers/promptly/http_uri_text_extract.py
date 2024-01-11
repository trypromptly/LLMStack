import logging
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import conint
from pydantic import Field

from llmstack.common.blocks.data.store.vectorstore import Document, DocumentQuery
from llmstack.common.blocks.data.store.vectorstore.chroma import Chroma
from llmstack.common.utils.text_extract import extract_text_from_url, ExtraParams
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class HttpUriTextExtractorConfiguration(ApiProcessorSchema):
    document_limit: Optional[conint(ge=0, le=10)] = Field(
        description='The maximum number of documents to return', default=1, advanced_parameter=True,
    )
    text_chunk_size: Optional[conint(ge=500, le=2000)] = Field(
        description='Chunksize of document', default=1500, advanced_parameter=True,
    )


class HttpUriTextExtractorInput(ApiProcessorSchema):
    url: str = Field(
        default='', description='The URL to extract text from', widget='text',
    )
    query: Optional[str] = Field(
        default='', description='The query to search the document',
    )


class HttpUriTextExtractorOutput(ApiProcessorSchema):
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

    @staticmethod
    def name() -> str:
        return 'URL Extractor'

    @staticmethod
    def slug() -> str:
        return 'http_uri_text_extract'

    @staticmethod
    def description() -> str:
        return 'Extracts text from a given URL. Links can point to YouTube, PDF, PPTX, DOC, TEXT or XML files'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def session_data_to_persist(self) -> dict:
        return {
            'url': self.url,
            'extracted_text': self.extracted_text,
        }

    def process(self) -> HttpUriTextExtractorOutput:
        openai_api_key = self._env.get('openai_api_key', None)

        query = self._input.query
        url = self._input.url.strip().rstrip()

        if (query is None or query == '') and url == self.url and self.extracted_text is not None:
            async_to_sync(self._output_stream.write)(
                HttpUriTextExtractorOutput(text=self.extracted_text),
            )
            output = self._output_stream.finalize()
            return output

        if query and self.storage_index_name and url == self.url:
            self.temp_store = Chroma(is_persistent=False)

            documents: List[Document] = self.temp_store.hybrid_search(
                self.storage_index_name, document_query=DocumentQuery(
                    query=query, limit=self._config.document_limit),
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
                self.temp_store.add_text(
                    index_name, Document(page_content_key="content", page_content=text_chunk, metadata={
                                         'source': self.url}),
                )
            documents: List[Document] = self.temp_store.hybrid_search(
                self.storage_index_name, document_query=DocumentQuery(
                    query=query, limit=self._config.document_limit),
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
