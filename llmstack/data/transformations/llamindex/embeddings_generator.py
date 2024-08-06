import json
import logging
from typing import Any, Dict, List, Optional

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from llmstack.data.transformations.llamindex.base import LlamaIndexTransformers

logger = logging.getLogger(__name__)


def get_embedding_client(datasource, embedding_provider_slug, embedding_model_name):
    embedding_model = "text-embedding-ada-002" if embedding_model_name == "ada" else embedding_model_name

    if not embedding_provider_slug:
        raise ValueError("embedding_provider_slug is required")

    if embedding_provider_slug == "openai":
        provider_config = datasource.profile.get_provider_config(model_slug=embedding_model, provider_slug="openai")
        return OpenAIEmbedding(
            api_key=provider_config.api_key, model=embedding_model, api_base=provider_config.base_url
        )
    elif embedding_provider_slug == "azure-openai":
        provider_config = datasource.profile.get_provider_config(model_slug=embedding_model, provider_slug="azure")
        return AzureOpenAIEmbedding(
            model=embedding_model,
            api_key=provider_config.api_key,
            azure_endpoint=provider_config.azure_endpoint if provider_config.azure_endpoint else None,
            deployment_name=provider_config.azure_deployment if provider_config.azure_deployment else None,
            api_version=provider_config.api_version if provider_config.api_version else "2024-02-01",
        )


class EmbeddingsGenerator(BaseEmbedding, LlamaIndexTransformers):
    embedding_provider_slug: Optional[str] = None
    embedding_model_name: str = "ada"
    additional_kwargs: Optional[Dict[str, Any]] = None

    @classmethod
    def slug(cls):
        return "embeddings-generator"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    @classmethod
    def get_schema(cls):
        json_schema = json.loads(cls.schema_json())
        # Remove all values in properties except embedding_provider_slug, embedding_model_name, and additional_kwargs
        property_keys = list(json_schema["properties"].keys())
        for key in property_keys:
            if key not in ["embedding_provider_slug", "embedding_model_name", "additional_kwargs"]:
                json_schema["properties"].pop(key)
        return json_schema

    @classmethod
    def class_name(cls) -> str:
        return "EmbeddingsGenerator"

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""
        client = get_embedding_client(
            datasource=self.additional_kwargs["datasource"],
            embedding_provider_slug=self.embedding_provider_slug,
            embedding_model_name=self.embedding_model_name,
        )

        return client._get_query_embedding(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        raise NotImplementedError

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        client = get_embedding_client(
            datasource=self.additional_kwargs["datasource"],
            embedding_provider_slug=self.embedding_provider_slug,
            embedding_model_name=self.embedding_model_name,
        )

        return client._get_text_embedding(text)

    def get_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)
