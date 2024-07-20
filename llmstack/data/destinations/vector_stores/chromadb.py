from typing import Dict, List, Optional

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore as _ChromaVectorStore
from pydantic import BaseModel

from llmstack.data.destinations.base import BaseDestination


class ChromaVectorStore(_ChromaVectorStore):
    def add(self, nodes, **add_kwargs) -> List[str]:
        from chromadb.utils import embedding_functions

        for node in nodes:
            if node.embedding is None:
                node.embedding = embedding_functions.DefaultEmbeddingFunction()([node.text])[0]

        return super().add(nodes, **add_kwargs)

    def delete_index(self):
        self._collection._client.delete_collection(self.collection_name)


class ChromaSettings(BaseModel):
    key: str
    value: str


class ChromaDB(BaseDestination):
    path: str
    index_name: str
    text_key: Optional[str] = "content"
    settings: List[ChromaSettings] = []

    @classmethod
    def slug(cls):
        return "chroma_vector_store"

    @classmethod
    def provider_slug(cls):
        return "chroma"

    def settings_dict(self) -> Dict[str, str]:
        return {setting.key: setting.value for setting in self.settings}

    def initialize_client(self, *args, **kwargs):
        client = chromadb.PersistentClient(path=self.path, settings=chromadb.config.Settings(**self.settings_dict))
        chroma_collection = client.get_or_create_collection(self.index_name)
        self._client = ChromaVectorStore(chroma_collection=chroma_collection)
