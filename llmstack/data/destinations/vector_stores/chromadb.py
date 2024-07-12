from typing import Any, Dict, List, Literal

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

from llmstack.data.vector_stores.base import VectorStoreConfiguration


class PromptlyChromaVectorStore(ChromaVectorStore):
    def add(self, nodes, **add_kwargs) -> List[str]:
        from chromadb.utils import embedding_functions

        for node in nodes:
            if node.embedding is None:
                node.embedding = embedding_functions.DefaultEmbeddingFunction()([node.text])[0]

        return super().add(nodes, **add_kwargs)

    def delete_index(self):
        self._collection._client.delete_collection(self.collection_name)


class ChromaDBVectorStoreConfiguration(VectorStoreConfiguration):
    type: Literal["chromadb"] = "chromadb"
    path: str
    settings: Dict[str, Any]

    def initialize_client(self, *args, **kwargs) -> PromptlyChromaVectorStore:
        client = chromadb.PersistentClient(path=self.path, settings=chromadb.config.Settings(**self.settings))
        chroma_collection = client.get_or_create_collection(kwargs.get("index_name", "text"))
        return PromptlyChromaVectorStore(chroma_collection=chroma_collection)
