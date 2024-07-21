import json
import logging
import uuid
from string import Template
from typing import Any, Dict, List, Optional, cast

import weaviate
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores.types import (
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
from llmstack.data.schemas import DataDocument
from llmstack.processors.providers.weaviate import (
    APIKey,
    WeaviateLocalInstance,
    WeaviateProviderConfig,
)

logger = logging.getLogger(__name__)
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


class WeaviateVectorStore:
    def __init__(
        self,
        weaviate_client: Optional[Any] = None,
        index_name: Optional[str] = None,
        text_key: str = "content",
        auth_config: Optional[Any] = None,
    ) -> None:
        """Initialize params."""
        index_name = index_name or f"Datasource_{uuid.uuid4().hex}"
        if not index_name[0].isupper():
            raise ValueError("Index name must start with a capital letter, e.g. 'LlamaIndex'")

        self._index_name = index_name
        self._text_key = text_key
        self._auth_config = auth_config
        self._client = cast(weaviate.WeaviateClient, weaviate_client)

    @classmethod
    def class_name(cls) -> str:
        return "WeaviateVectorStore"

    @property
    def client(self) -> weaviate.WeaviateClient:
        """Get client."""
        return self._client

    def get_nodes(
        self, node_ids: Optional[List[str]] = None, filters: Optional[MetadataFilters] = None
    ) -> List[BaseNode]:
        result = []
        logger.info(f"Fetching nodes from Weaviate with ids: {node_ids}")
        for node_id in node_ids:
            try:
                schema_client = self.client.collections.get(self._index_name)
                logger.info(f"Fetching node with id: {schema_client.query.fetch_objects()}")
                object_data = schema_client.query.fetch_object_by_id(uuid=node_id)

                if object_data:
                    result.append(
                        TextNode(
                            id_=node_id,
                            text=object_data.properties.get(self._text_key, ""),
                            metadata={k: v for k, v in object_data.properties.items() if k != self._text_key},
                        )
                    )
            except weaviate.exceptions.UnexpectedStatusCodeException:
                pass
        return result

    def add(self, nodes: List[BaseNode]) -> List[str]:
        """Add nodes to index.

        Args:
            nodes: List[BaseNode]: list of nodes with embeddings

        """
        ids = [r.node_id for r in nodes]
        schema_client = self.client.collections.get(self._index_name)

        with schema_client.batch.dynamic() as batch:
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
                    batch.add_object(properties=properties, uuid=id, vector=node.embedding)
                else:
                    batch.add_object(properties=properties, uuid=id)
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
    text_key: str = Field(description="Text key", default="Text")
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

        datasource = kwargs.get("datasource")

        schema = self.schema or WEAVIATE_SCHEMA.safe_substitute(class_name=self.index_name, content_key=self.text_key)
        self._schema_dict = json.loads(schema)

        try:
            self._deployment_config = datasource.profile.get_provider_config(
                deployment_key=self.deployment_name, provider_slug=self.provider_slug()
            )
        except Exception:
            # TODO: Reove this after migration of vector store settings is done to provider config

            auth = None
            if datasource.profile.weaviate_api_key:
                auth = APIKey(api_key=datasource.profile.weaviate_api_key)

            self._deployment_config = WeaviateProviderConfig(
                provider_slug="weaviate",
                instance=WeaviateLocalInstance(url=datasource.profile.weaviate_url),
                auth=auth,
                additional_headers=[],
                module_config=json.dumps(datasource.profile.weaviate_text2vec_config),
            )

        additional_headers = self._deployment_config.additional_headers_dict or {}
        if datasource.profile.vectostore_embedding_endpoint == "azure_openai":
            azure_deployment_config = datasource.profile.get_provider_config(provider_slug="azure")
            additional_headers["X-Azure-Api-Key"] = azure_deployment_config.api_key
        else:
            openai_deployment_config = datasource.profile.get_provider_config(provider_slug="openai")
            additional_headers["X-Openai-Api-Key"] = openai_deployment_config.api_key

        if self._deployment_config and self._deployment_config.module_config:
            self._schema_dict["classes"][0]["moduleConfig"] = json.loads(self._deployment_config.module_config)

        auth = None
        if isinstance(self._deployment_config.auth, APIKey):
            auth = weaviate.auth.AuthApiKey(api_key=self._deployment_config.auth.api_key)

        weaviate_client = None

        if isinstance(self._deployment_config.instance, WeaviateLocalInstance):
            if (
                self._deployment_config.instance.http_host
                and self._deployment_config.instance.http_port
                and self._deployment_config.instance.grpc_host
                and self._deployment_config.instance.grpc_port
            ):
                weaviate_client = connect_to_custom(
                    http_host=self._deployment_config.instance.http_host,
                    http_port=self._deployment_config.instance.http_port,
                    http_secure=self._deployment_config.instance.http_secure,
                    grpc_host=self._deployment_config.instance.grpc_host,
                    grpc_port=self._deployment_config.instance.grpc_port,
                    grpc_secure=self._deployment_config.instance.grpc_secure,
                    headers=additional_headers,
                    auth_credentials=auth,
                )
            elif self._deployment_config.instance.url:
                protocol, url = self._deployment_config.instance.url.split("://")
                host, port = url.split(":")
                logger.info(f"Connecting to Weaviate instance at {self._deployment_config.instance.url}")
                weaviate_client = weaviate.WeaviateClient(
                    connection_params=weaviate.connect.base.ConnectionParams(
                        http=weaviate.connect.base.ProtocolParams(host=host, port=port, secure=protocol == "https"),
                        grpc=weaviate.connect.base.ProtocolParams(host=host, port=50051, secure=protocol == "https"),
                    ),
                    auth_client_secret=auth,
                    additional_headers=additional_headers,
                )
        else:
            weaviate_client = connect_to_wcs(
                cluster_url=self._deployment_config.instance.cluster_url,
                auth_credentials=auth,
                headers=additional_headers,
            )

        weaviate_client.connect()

        self._client = WeaviateVectorStore(
            weaviate_client=weaviate_client,
            index_name=self.index_name,
            text_key=self.text_key,
            auth_config=self._deployment_config.auth,
        )

    def get_nodes(self, node_ids: Optional[List[str]] = None, filters: Optional[MetadataFilters] = None):
        return self._client.get_nodes(node_ids=node_ids, filters=filters)

    def add(self, document: DataDocument) -> DataDocument:
        return self._client.add(document.nodes)
