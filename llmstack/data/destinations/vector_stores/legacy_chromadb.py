from typing import Any, Dict, List, Literal, Optional

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

from llmstack.data.destinations.vector_stores.base import VectorStoreConfiguration


class PromptlyChromaVectorStore(ChromaVectorStore):
    def add(self, nodes, **add_kwargs) -> List[str]:
        from chromadb.utils import embedding_functions

        for node in nodes:
            if node.embedding is None:
                node.embedding = embedding_functions.DefaultEmbeddingFunction()([node.text])[0]

        return super().add(nodes, **add_kwargs)

    def delete_index(self):
        self._collection._client.delete_collection(self.collection_name)


class PromptlyLegacyChromaDBVectorStoreConfiguration(VectorStoreConfiguration):
    type: Literal["promptly_legacy_chromadb"] = "promptly_legacy_chromadb"
    path: str
    index_name: str
    text_key: Optional[str] = "content"
    settings: Dict[str, Any]

    @classmethod
    def slug(cls):
        return "promptly_legacy_chromadb"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def initialize_client(self, *args, **kwargs) -> PromptlyChromaVectorStore:
        client = chromadb.PersistentClient(path=self.path, settings=chromadb.config.Settings(**self.settings))
        chroma_collection = client.get_or_create_collection(self.index_name)
        return PromptlyChromaVectorStore(chroma_collection=chroma_collection)
