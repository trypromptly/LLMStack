from typing import Literal

from llama_index.vector_stores.chroma import ChromaVectorStore

from llmstack.datasources.vector_stores.base import VectorStoreConfiguration


class ChromaDBVectorStoreConfiguration(VectorStoreConfiguration):
    type: Literal["chromadb"] = "chromadb"

    def initialize_client(self) -> ChromaVectorStore:
        return ChromaVectorStore()
