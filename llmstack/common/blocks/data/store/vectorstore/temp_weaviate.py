import json
import logging
import uuid
from typing import Any

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.blocks.data.store.vectorstore import DocumentQuery
from llmstack.common.blocks.data.store.vectorstore.weaviate import Weaviate
from llmstack.common.blocks.data.store.vectorstore.weaviate import WeaviateConfiguration as BaseWeaviateConfiguration

logger = logging.getLogger(__name__)


class WeaviateConfiguration(BaseWeaviateConfiguration):
    pass


class TempWeaviate(Weaviate):
    CONTENT_KEY = 'content'

    """
    Weaviate VectorStore implementation.
    """

    """
    Weaviate VectorStore implementation to store temporary documents. Weaviate can use OpenAI, Cohere and HuggingFace API keys
    """

    def __init__(self, *args, **kwargs) -> None:

        self.weaviate_embedding_endpoint = kwargs.get(
            'weaviate_embedding_endpoint', None,
        )
        self.weaviate_text2vec_config = kwargs.get(
            'weaviate_text2vec_config', None,
        )

        super().__init__(
            url=kwargs.get('url', None),
            openai_key=kwargs.get('openai_key', None),
            azure_openai_key=kwargs.get('azure_openai_key', None),
            weaviate_rw_api_key=kwargs.get('weaviate_rw_api_key', None),
        )

    def add_content(self, index_name: str, content: str, **kwargs: Any):
        content = content
        document = Document(
            page_content_key=self.CONTENT_KEY, page_content=content, metadata={
                'source': kwargs.get('source', 'temp')},
        )
        return self.add_text(index_name, document, **kwargs)

    def create_temp_index(self):
        index_name = 'Temp_{}'.format(str(uuid.uuid4())).replace('-', '_')
        if self.weaviate_text2vec_config is None:
            raise Exception('Vector store embedding config is not set')
        schmea = {
            'classes': [
                {
                    'class': index_name,
                    'description': 'Text data source',
                    'vectorizer': 'text2vec-openai',
                    'moduleConfig': {'text2vec-openai': self.weaviate_text2vec_config},
                    'properties': [
                        {
                            'name': self.CONTENT_KEY,
                            'dataType': ['text'],
                            'description': 'Text',
                            'moduleConfig': {'text2vec-openai': {'skip': False, 'vectorizePropertyName': False}},
                        },
                        {
                            'name': 'source', 'dataType': [
                                'string',
                            ], 'description': 'Document source',
                        },
                        {
                            'name': 'metadata', 'dataType': [
                                'string[]',
                            ], 'description': 'Document metadata',
                        },
                    ],
                },
            ],
        }

        self.create_index(json.dumps(schmea))
        return index_name

    def search_temp_index(self, index_name: str, query: str, limit: int):
        document_query = DocumentQuery(
            query=query, page_content_key=self.CONTENT_KEY, limit=limit, metadata={
                'additional_properties': ['source'],
            },
        )
        return self.similarity_search(index_name, document_query)
