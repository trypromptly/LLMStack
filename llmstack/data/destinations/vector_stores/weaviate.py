from typing import Optional

from pydantic import Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.processors.providers.weaviate import APIKey, WeaviateProviderConfig


class Weaviate(BaseDestination):
    index_name: str = Field(description="Index/Collection name", default="text")
    text_key: str = Field(description="Text key", default="text")
    deployment_name: Optional[str] = Field(description="Deployment name", default="default")

    _deployment_config: Optional[WeaviateProviderConfig] = PrivateAttr()

    @classmethod
    def slug(cls):
        return "weaviate"

    @classmethod
    def provider_slug(cls):
        return "weaviate"

    def initialize_client(self, *args, **kwargs):
        import weaviate
        from weaviate.connect.helpers import connect_to_custom

        datasource = kwargs.get("datasource")
        self._deployment_config = datasource.profile.get_provider_config(
            model_slug=self.slug(), deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )
        auth = None
        if isinstance(self._deployment_config.auth, APIKey):
            auth = weaviate.auth.AuthApiKey(api_key=self._deployment_config.auth.api_key)

        self._client = connect_to_custom(
            http_host=self._deployment_config.http_host,
            http_port=self._deployment_config.http_port,
            http_secure=self._deployment_config.http_secure,
            grpc_host=self._deployment_config.grpc_host,
            grpc_port=self._deployment_config.grpc_port,
            grpc_secure=self._deployment_config.grpc_secure,
            headers=self._deployment_config.additional_headers_dict,
            auth_credentials=auth,
        )
