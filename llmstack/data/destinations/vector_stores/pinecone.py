from typing import Optional

from pydantic import Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.processors.providers.pinecone import PineconeProviderConfig


class Pinecone(BaseDestination):
    index_name: str = Field(description="Index/Collection name", default="text")
    text_key: str = Field(description="Text key", default="text")
    namespace: Optional[str] = Field(description="Namespace", default=None)
    deployment_name: Optional[str] = Field(description="Deployment name", default="default")

    _deployment_config: Optional[PineconeProviderConfig] = PrivateAttr()

    def initialize_client(self, *args, **kwargs):
        from llama_index.vector_stores.pinecone import PineconeVectorStore

        datasource = kwargs.get("datasource")
        self._deployment_config = datasource.profile.get_provider_config(
            model_slug=self.slug(), deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )
        self._client = PineconeVectorStore(
            api_key=self._deployment_config.api_key.api_key,
            index_name=self.index_name,
            environment=self._deployment_config.environment,
            namespace=self.namespace,
            text_key=self.text_key,
        )
