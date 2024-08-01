from typing import Any, Dict, Optional

from pydantic import PrivateAttr

from llmstack.data.destinations.base import BaseDestination


class PromptlyVectorStore(BaseDestination):
    store_provider_slug: Optional[str] = None
    store_processor_slug: Optional[str] = None
    additional_kwargs: Optional[Dict[str, Any]] = {}

    _store: Optional[BaseDestination] = PrivateAttr(default=None)

    @classmethod
    def slug(cls):
        return "vector-store"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def initialize_client(self, *args, **kwargs):
        from llmstack.data.destinations.vector_stores.weaviate import Weaviate

        if not self.store_provider_slug:
            raise ValueError("store_provider_slug is required")

        if self.store_provider_slug == "weaviate":
            self._store = Weaviate(**self.additional_kwargs)
        else:
            raise ValueError(f"store_provider_slug {self.store_provider_slug} is not supported")
        self._store.initialize_client(*args, **kwargs)

    def add(self, document):
        return self._store.add(document)

    def delete(self, document):
        return self._store.delete(document)

    def search(self, query: str, **kwargs):
        return self._store.search(query, **kwargs)

    def create_collection(self):
        return self._store.create_collection()

    def delete_collection(self):
        return self._store.delete_collection()

    def get_nodes(self, node_ids=None, filters=None):
        return self._store.get_nodes(node_ids=node_ids, filters=filters)
