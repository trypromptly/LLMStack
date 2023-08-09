import logging
from typing import Any
from typing import List
from uuid import uuid4

import chromadb
from pydantic import BaseModel

from common.promptly.vectorstore import Document
from common.promptly.vectorstore import DocumentQuery
from common.promptly.vectorstore import VectorStoreInterface

logger = logging.getLogger(__name__)


class ChromaConfiguration(BaseModel):
    _type = 'Chroma'


class Chroma(VectorStoreInterface):
    """
    Chroma VectorStore implementation.
    """

    def __init__(self, *args, **kwargs) -> None:
        configuration = ChromaConfiguration(**kwargs)
        self._client = chromadb.Client()

    def add_text(self, index_name: str, document: Document, **kwargs: Any):
        content_key = document.page_content_key
        content = document.page_content
        metadata = document.metadata
        properties = {content_key: content}
        for metadata_key in metadata.keys():
            properties[metadata_key] = metadata[metadata_key]
        collection = self._client.get_collection(index_name)
        id = str(uuid4())
        if 'embeddings' in properties:
            collection.add(
                documents=[
                    properties.pop(
                    content_key,
                    ),
                ], metadatas=[properties], ids=[id], embeddings=[properties.pop('embeddings')],
            )
        else:
            collection.add(
                documents=[
                    properties.pop(
                    content_key,
                    ),
                ], metadatas=[properties], ids=[id],
            )
        return id

    def add_texts(self, index_name: str, documents: List[Document], **kwargs: Any):
        ids = []
        for document in documents:
            ids.append(self.add_text(index_name, document, kwargs))
        return ids

    def get_or_create_index(self, index_name: str, schema: str, **kwargs: Any):
        return self._client.get_or_create_collection(index_name)

    def create_index(self, schema: str, **kwargs: Any):
        return self._client.create_collection(kwargs['index_name'])

    def delete_index(self, index_name: str, **kwargs: Any):
        return self._client.delete_collection(index_name)

    def delete_document(self, document_id: str, **kwargs: Any):
        collection = self._client.get_collection(kwargs['index_name'])
        collection.delete([document_id])

    def similarity_search(self, index_name: str, document_query: DocumentQuery, **kwargs: Any):
        result = []
        collection = self._client.get_collection(index_name)
        search_result = collection.query(
            query_texts=[document_query.query], n_results=document_query.limit,
        )
        for index in range(len(search_result['documents'])):
            document_content = search_result['documents'][index][0]
            metadata = search_result['metadatas'][index][0]
            result.append(
                Document('', document_content, metadata),
            )

        return result

    def get_document_by_id(self, document_id: str, **kwargs: Any):
        collection = self._client.get_collection(kwargs['index_name'])
        document = collection.get(
            [document_id], include=[
            'documents', 'metadatas', 'embeddings',
            ],
        ).get(ids=[document_id])
        return Document('', document[0][0], document[1][0])

    def get_document_by_index(self, index_name: str, **kwargs: Any):
        results = []
        collection = self._client.get_collection(index_name)
        document_count = collection.count()
        result = collection.peek(limit=document_count)
        for index in range(len(result['ids'])):
            results.append(
                Document(
                'content', result['documents'][index], {**result['metadatas'][index], 'embeddings': result['embeddings'][index], 'id': result['ids'][index]},
                ),
            )
        return results
