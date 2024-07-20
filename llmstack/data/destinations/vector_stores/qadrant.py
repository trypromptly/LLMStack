from typing import Optional

from llama_index.vector_stores.qdrant import QdrantVectorStore
from pydantic import Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.processors.providers.qdrant import QdrantProviderConfig


class Qdrant(BaseDestination):
    index_name: str = Field(description="Index/Collection name", default="text")
    text_key: Optional[str] = Field(description="Text key", default="text")
    deployment_name: Optional[str] = Field(description="Deployment name", default="default")

    _deployment_config: Optional[QdrantProviderConfig] = PrivateAttr()

    def initialize_client(self, *args, **kwargs):
        import qdrant_client

        datasource = kwargs.get("datasource")
        self._deployment_config = datasource.profile.get_provider_config(
            model_slug=self.slug(), deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )
        client = qdrant_client.QdrantClient(
            location=self._deployment_config.location,
            url=self._deployment_config.url,
            port=self._deployment_config.port,
            grpc_port=self._deployment_config.grpc_port,
            api_key=self._deployment_config.api_key.api_key,
        )

        self._client = QdrantVectorStore(
            collection_name=self.index_name,
            client=client,
        )
