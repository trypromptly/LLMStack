import json
from typing import Any, Dict, List, Optional

from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import PrivateAttr

from llmstack.data.transformations.llamindex.base import LlamaIndexTransformers


def get_embedding(client, text, engine, **kwargs):
    return []


class EmbeddingsGenerator(BaseEmbedding, LlamaIndexTransformers):
    embedding_provider_slug: Optional[str] = None
    embedding_model_name: str = "ada"
    additional_kwargs: Optional[Dict[str, Any]] = None

    _query_engine: str = PrivateAttr()
    _text_engine: str = PrivateAttr()
    _client: Optional[Any] = PrivateAttr()

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
        client = self._get_client()
        return get_embedding(
            client,
            query,
            engine=self._query_engine,
            **self.additional_kwargs,
        )

    async def _aget_query_embedding(self, query: str) -> List[float]:
        raise NotImplementedError

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        client = self._get_client()
        return get_embedding(
            client,
            text,
            engine=self._text_engine,
            **self.additional_kwargs,
        )
