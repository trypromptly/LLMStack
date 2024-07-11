from typing import Literal

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

from llmstack.datasources.vector_stores.base import VectorStoreConfiguration


class ChromaDBVectorStoreConfiguration(VectorStoreConfiguration):
    type: Literal["chromadb"] = "chromadb"

    def initialize_client(self, *args, **kwargs) -> ChromaVectorStore:
        client = chromadb.EphemeralClient()
        chroma_collection = client.get_or_create_collection(kwargs.get("index_name", "text"))
        return ChromaVectorStore(chroma_collection=chroma_collection)
