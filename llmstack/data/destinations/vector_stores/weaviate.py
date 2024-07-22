import json
import logging
import uuid
from string import Template
from typing import Any, Dict, List, Optional

import weaviate
import weaviate.classes as wvc
from llama_index.core.schema import TextNode
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
    text = entry.get("properties", {}).get(text_key, "")
    source = entry.get("properties", {}).get("source", None)

    try:
        node = metadata_dict_to_node(entry["metadata"])
        node.text = text
        node.embedding = None

    except Exception:
        logger.error("Error in converting to node")
        metadata, node_info, relationships = legacy_metadata_dict_to_node(entry)
        source = entry.get("properties", {}).get("source", None)

        node = TextNode(
            text=text,
            id_=str(entry["uuid"]),
            metadata={"source": source},
            start_char_idx=node_info.get("start", None),
            end_char_idx=node_info.get("end", None),
            relationships=relationships,
            embedding=None,
        )
    node.metadata["source"] = source
    return node


class WeaviateVectorStore:
    def __init__(
        self,
        weaviate_client: Optional[weaviate.WeaviateClient] = None,
        index_name: Optional[str] = None,
        text_key: str = "content",
        auth_config: Optional[Any] = None,
    ) -> None:
        """Initialize params."""
        index_name = index_name or f"Datasource_{uuid.uuid4().hex}"
        self._index_name = index_name
        self._text_key = text_key
        self._auth_config = auth_config
        self._weaviate_client = weaviate_client
        self._client = weaviate_client.collections.get(self._index_name)

    @classmethod
    def class_name(cls) -> str:
        return "WeaviateVectorStore"

    @property
    def client(self) -> weaviate.collections.Collection:
        """Get client."""
        return self._client

    def get_nodes(self, node_ids: Optional[List[str]] = None, filters: Optional[MetadataFilters] = None):
        result = []
        for node_id in node_ids:
            try:
                object_data = self.client.query.fetch_object_by_id(uuid=node_id)
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

    def add(self, nodes) -> List[str]:
        """Add nodes to index.

        Args:
            nodes: List[BaseNode]: list of nodes with embeddings

        """
        ids = [r.node_id for r in nodes]

        with self.client.batch.dynamic() as batch:
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

    def delete(self, ref_doc_id: str) -> None:
        self.client.data.delete_by_id(uuid=ref_doc_id)

    def delete_index(self) -> None:
        self._weaviate_client.collections.delete(self._index_name)

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        nodes = []
        node_ids = []
        similarities = []

        if query.mode == VectorStoreQueryMode.HYBRID:
            try:
                query_response = self.client.query.hybrid(
                    query=query.query_str,
                    alpha=query.alpha,
                    query_properties=[self._text_key],
                    return_metadata=None,
                )
            except Exception as e:
                raise e

        else:
            try:
                query_response = self.client.query.near_text(
                    query=query.query_str,
                    certainty=kwargs.get("search_distance", None),
                    limit=query.similarity_top_k if query.similarity_top_k is not None else 10,
                    return_metadata=wvc.query.MetadataQuery(certainty=True, distance=True),
                )
            except Exception as e:
                raise e

        if not query_response or not query_response.objects:
            raise Exception("Error in fetching data from document store")

        for entry in query_response.objects:
            node = to_node(entry.__dict__, text_key=self._text_key)
            nodes.append(node)
            node_ids.append(nodes[-1].node_id)

        return VectorStoreQueryResult(nodes=nodes, ids=node_ids, similarities=similarities)


class Weaviate(BaseDestination):
    index_name: str = Field(description="Index/Collection name", default="text")
    text_key: str = Field(description="Text key", default="Text")
    deployment_name: Optional[str] = Field(description="Deployment name", default="*")
    weaviate_schema: Optional[str] = Field(description="Schema", default="")

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

        schema = self.weaviate_schema or WEAVIATE_SCHEMA.safe_substitute(
            class_name=self.index_name, content_key=self.text_key
        )
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

    def add(self, document: DataDocument) -> DataDocument:
        return self._client.add(document.nodes)

    def delete(self, document: DataDocument) -> DataDocument:
        for node in document.nodes:
            self._client.delete(node.node_id)

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

    def create_collection(self):
        pass

    def delete_collection(self):
        return self._client.delete_index()

    def get_nodes(self, node_ids: Optional[List[str]] = None, filters: Optional[MetadataFilters] = None):
        return self._client.get_nodes(node_ids=node_ids, filters=filters)
