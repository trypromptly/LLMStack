import json
import uuid
from string import Template
from typing import Any, Dict, List, Optional

import weaviate
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)
from llama_index.core.vector_stores.utils import (
    legacy_metadata_dict_to_node,
    metadata_dict_to_node,
)
from pydantic import Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.processors.providers.weaviate import (
    APIKey,
    WeaviateLocalInstance,
    WeaviateProviderConfig,
)

WEAVIATE_SCHEMA = Template(
    """
{
    "classes": [
        {
            "class": "$class_name",
            "description": "Text data source",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "type": "text"
                }
            },
            "vectorIndexConfig": {
                "pq": {
                    "enabled": true
                }
            },
            "replicationConfig": {
                "factor": 1
            },
            "shardingConfig": {
                "desiredCount": 1
            },
            "properties": [
                {
                    "name": "$content_key",
                    "dataType": [
                        "text"
                    ],
                    "description": "Text",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": false,
                            "vectorizePropertyName": false
                        }
                    }
                },
                {
                    "name": "source",
                    "dataType": [
                        "string"
                    ],
                    "description": "Document source"
                },
                {
                    "name": "metadata",
                    "dataType": [
                        "string[]"
                    ],
                    "description": "Document metadata"
                }
            ]
        }
    ]
}
""",
)


def to_node(entry: Dict, text_key: str = "Text") -> TextNode:
    """Convert to Node."""
    text = entry.pop(text_key, "")

    try:
        node = metadata_dict_to_node(entry["metadata"])
        node.text = text
        node.embedding = None
    except Exception:
        metadata, node_info, relationships = legacy_metadata_dict_to_node(entry)

        node = TextNode(
            text=text,
            id_=entry.get("_additional", {}).get("id", str(uuid.uuid4())),
            metadata=metadata,
            start_char_idx=node_info.get("start", None),
            end_char_idx=node_info.get("end", None),
            relationships=relationships,
            embedding=None,
        )
    return node


class WeaviateVectorStore(BasePydanticVectorStore):
    stores_text: bool = True

    _client = PrivateAttr()
    _index_name = PrivateAttr()
    _text_key = PrivateAttr()
    _schema = PrivateAttr()

    def __init__(
        self,
        weaviate_client: Optional[Any] = None,
        index_name: str = "Text",
        text_key: str = "content",
        auth_config: Optional[Any] = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
        schema: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        self._client = weaviate_client

        self._schema = schema

        if not index_name[0].isupper():
            raise ValueError("Index name must start with a capital letter, e.g. 'Text'")

        self._text_key = text_key
        super().__init__(
            url=url,
            index_name=index_name,
            text_key=text_key,
            auth_config=auth_config.__dict__ if auth_config else {},
            client_kwargs=client_kwargs or {},
        )

    @property
    def client(self) -> Any:
        """Get client."""
        return self._client

    @classmethod
    def class_name(cls) -> str:
        return "WeaviateVectorStore"

    def get_nodes(
        self, node_ids: Optional[List[str]] = None, filters: Optional[MetadataFilters] = None
    ) -> List[BaseNode]:
        result = []
        for node_id in node_ids:
            try:
                object_data = self.client.data_object.get_by_id(node_id, class_name=self._index_name)
                if object_data:
                    result.append(
                        TextNode(
                            id_=node_id,
                            text=object_data["properties"].get(self._text_key, ""),
                            metadata={k: v for k, v in object_data["properties"].items() if k != self._text_key},
                        )
                    )
            except weaviate.exceptions.UnexpectedStatusCodeException:
                pass
        return result

    def add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """Add nodes to index.

        Args:
            nodes: List[BaseNode]: list of nodes with embeddings

        """
        ids = [r.node_id for r in nodes]
        with self.client.batch as batch:
            for node in nodes:
                content_key = self._text_key
                content = node.text
                metadata = node.metadata
                id = node.node_id
                properties = {content_key: content}
                for metadata_key in metadata.keys():
                    properties[metadata_key] = metadata[metadata_key]
                if node.embedding:
                    # Vectors we provided with the document use them
                    batch.add_data_object(properties, self._index_name, id, vector=node.embedding)
                else:
                    batch.add_data_object(properties, self._index_name, id)
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        self._client.data_object.delete(ref_doc_id, self._index_name)

    def delete_index(self) -> None:
        self._client.schema.delete_class(self._index_name)

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        nodes = []
        node_ids = []
        similarities = []

        if query.mode == VectorStoreQueryMode.HYBRID:
            try:
                query_obj = self._client.query.get(self._index_name, [self._text_key, "source"])
                query_response = (
                    query_obj.with_hybrid(query=query.query_str, alpha=query.alpha)
                    .with_limit(query.hybrid_top_k)
                    .with_additional(["id", "score"])
                    .do()
                )
            except Exception as e:
                raise e

        else:
            nearText = {"concepts": [query.query_str]}
            if kwargs.get("search_distance"):
                nearText["certainty"] = kwargs.get("search_distance")
            try:
                query_obj = self.client.query.get(self._index_name, [self._text_key, "source"])
                query_response = (
                    query_obj.with_near_text(nearText)
                    .with_limit(query.similarity_top_k if query.similarity_top_k is not None else 10)
                    .with_additional(["id", "certainty", "distance"])
                    .do()
                )
            except Exception as e:
                raise e
        if (
            "data" not in query_response
            or "Get" not in query_response["data"]
            or self._index_name not in query_response["data"]["Get"]
        ):
            raise Exception("Error in fetching data from document store")
        if query_response["data"]["Get"][self._index_name]:
            for res in query_response["data"]["Get"][self._index_name]:
                res["metadata"] = dict({"source": res["source"]})
                nodes.append(to_node(res, text_key=self._text_key))
                node_ids.append(nodes[-1].node_id)

        return VectorStoreQueryResult(nodes=nodes, ids=node_ids, similarities=similarities)


class Weaviate(BaseDestination):
    index_name: str = Field(description="Index/Collection name", default="text")
    text_key: str = Field(description="Text key", default="text")
    deployment_name: Optional[str] = Field(description="Deployment name", default="*")
    schema: Optional[str] = Field(description="Schema", default="")

    _deployment_config: Optional[WeaviateProviderConfig] = PrivateAttr()
    _schema_dict = PrivateAttr()

    @classmethod
    def slug(cls):
        return "weaviate_vector_store"

    @classmethod
    def provider_slug(cls):
        return "weaviate"

    def initialize_client(self, *args, **kwargs):
        import weaviate
        from weaviate.connect.helpers import connect_to_custom, connect_to_wcs

        schema = self.schema or WEAVIATE_SCHEMA.safe_substitute(class_name=self.index_name, content_key=self.text_key)
        self._schema_dict = json.loads(schema)

        datasource = kwargs.get("datasource")
        self._deployment_config = datasource.profile.get_provider_config(
            deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )

        additional_headers = self._deployment_config.additional_headers_dict or {}

        if datasource.profile.vectostore_embedding_endpoint == "openai":
            openai_provider_config = datasource.profile.get_provider_config(provider_slug="openai")
            additional_headers["X-OpenAI-Api-Key"] = openai_provider_config.api_key

        else:
            azure_provider_config = datasource.profile.get_provider_config(provider_slug="azure")
            additional_headers["X-Azure-Api-Key"] = azure_provider_config.api_key

        if self._deployment_config and self._deployment_config.module_config:
            self._schema_dict["classes"][0]["moduleConfig"] = json.loads(self._deployment_config.module_config)

        auth = None
        if isinstance(self._deployment_config.auth, APIKey):
            auth = weaviate.auth.AuthApiKey(api_key=self._deployment_config.auth.api_key)

        weaviate_client = (
            connect_to_custom(
                http_host=self._deployment_config.instance.http_host,
                http_port=self._deployment_config.instance.http_port,
                http_secure=self._deployment_config.instance.http_secure,
                grpc_host=self._deployment_config.instance.grpc_host,
                grpc_port=self._deployment_config.instance.grpc_port,
                grpc_secure=self._deployment_config.instance.grpc_secure,
                headers=self._deployment_config.additional_headers_dict,
                auth_credentials=auth,
            )
            if isinstance(self._deployment_config.instance, WeaviateLocalInstance)
            else connect_to_wcs(
                cluster_url=self._deployment_config.instance.cluster_url,
                auth_credentials=auth,
                headers=self._deployment_config.additional_headers_dict,
            )
        )

        self._client = WeaviateVectorStore(
            weaviate_client=weaviate_client,
            index_name=self.index_name,
            text_key=self.text_key,
            auth_config=self._deployment_config.auth,
            schema=self._schema_dict,
        )
