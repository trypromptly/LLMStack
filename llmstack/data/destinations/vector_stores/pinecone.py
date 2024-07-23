from typing import Optional

from pydantic import Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.processors.providers.pinecone import PineconeProviderConfig


class Pinecone(BaseDestination):
    index_name: str = Field(description="Index/Collection name", default="text")
    text_key: str = Field(description="Text key", default="text")
    deployment_name: Optional[str] = Field(description="Deployment name", default="*")

    _deployment_config: Optional[PineconeProviderConfig] = PrivateAttr()

    @classmethod
    def slug(cls):
        return "pinecone_vector_store"

    @classmethod
    def provider_slug(cls):
        return "pinecone"

    def initialize_client(self, *args, **kwargs):
        from llama_index.vector_stores.pinecone import PineconeVectorStore
        from pinecone import Pinecone as _Pinecone

        datasource = kwargs.get("datasource")
        self._deployment_config = datasource.profile.get_provider_config(
            model_slug=self.slug(), deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )

        pinecone_client = _Pinecone(api_key=self._deployment_config.auth.api_key)
        pinecone_index = pinecone_client.Index(self.index_name)

        self._client = PineconeVectorStore(
            pinecone_index=pinecone_index,
            api_key=self._deployment_config.auth.api_key,
            index_name=self.index_name,
            text_key=self.text_key,
        )

    def search(self, query: str, **kwargs):
        from llama_index.core.vector_stores.types import (
            VectorStoreQuery,
            VectorStoreQueryMode,
        )

        vector_store_query = VectorStoreQuery(
            query_str=query,
            mode=(
                VectorStoreQueryMode.HYBRID if kwargs.get("use_hybrid_search", False) else VectorStoreQueryMode.DEFAULT
            ),
            alpha=kwargs.get("alpha", 0.75),
            hybrid_top_k=kwargs.get("limit", 2),
        )

        return self._client.query(query=vector_store_query)
