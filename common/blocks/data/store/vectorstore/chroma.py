import logging
from typing import Any, Tuple
from typing import List
from uuid import uuid4

import chromadb
from pydantic import BaseModel
from django.conf import settings

from common.blocks.data.store.vectorstore import Document
from common.blocks.data.store.vectorstore import DocumentQuery
from common.blocks.data.store.vectorstore import VectorStoreInterface


class ChromaConfiguration(BaseModel):
    _type = 'Chroma'
    anonymized_telemetry = False


class Chroma(VectorStoreInterface):
    """
    Chroma VectorStore implementation.
    """

    def __init__(self, *args, **kwargs) -> None:
        configuration = ChromaConfiguration(**kwargs)
        db_settings = chromadb.config.Settings(**configuration.dict())
        self._client = chromadb.PersistentClient(
            path=settings.DEFAULT_VECTOR_DATABASE_PATH, settings=db_settings) if settings.DEFAULT_VECTOR_DATABASE_PATH else chromadb.Client(settings=db_settings)

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
            ids.append(self.add_text(index_name, document, kwargs=kwargs))
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

    def get_document_by_id(self, index_name: str, document_id: str, content_key: str):
        collection = self._client.get_collection(index_name)
        result = collection.get(
            [document_id], include=[
                'documents', 'metadatas', 'embeddings',
            ],
        )
        return Document(content_key, result['documents'][0] if len(result['documents']) > 0 else None, {
            **result['metadatas'][0]} if len(result['metadatas']) > 0 else None)

    def hybrid_search(self, index_name: str, document_query: DocumentQuery, **kwargs) -> List[Tuple[int, float]]:
        return self.similarity_search(index_name, document_query, **kwargs)

    def similarity_search(self, index_name: str, document_query: DocumentQuery, **kwargs: Any):
        result = []
        collection = self._client.get_collection(index_name)
        search_result = collection.query(
            query_texts=[document_query.query], n_results=document_query.limit,
        )
        for index in range(len(search_result['documents'])):
            document_content = search_result['documents'][index][0]
            metadata = search_result['metadatas'][index][0]
            metadata['distance'] = search_result['distances'][index][0] if len(
                search_result['distances']) > 0 else -1
            result.append(
                Document('', document_content, metadata),
            )

        return result
