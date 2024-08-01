import json
import logging
import uuid
from typing import Any, Dict, List, Optional

import weaviate
import weaviate.classes as wvc
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import (
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)
from llama_index.core.vector_stores.utils import (
    legacy_metadata_dict_to_node,
    metadata_dict_to_node,
)
from llama_index.vector_stores.weaviate.base import _to_weaviate_filter
from pydantic import Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.data.schemas import DataDocument
from llmstack.processors.providers.weaviate import (
    APIKey,
    EmbeddingsProvider,
    WeaviateLocalInstance,
    WeaviateProviderConfig,
)

logger = logging.getLogger(__name__)


def to_node(entry: Dict, text_key: str = "Text") -> TextNode:
    """Convert to Node."""
    text = entry.get("properties", {}).get(text_key, "")
    source = entry.get("properties", {}).get("source", None)

    try:
        node = metadata_dict_to_node(entry["metadata"])
        node.text = text
        node.embedding = None

    except Exception:
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

    @classmethod
    def class_name(cls) -> str:
        return "WeaviateVectorStore"

    @property
    def client(self) -> weaviate.collections.Collection:
        """Get client."""
        self._client = self._weaviate_client.collections.get(self._index_name)
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

    def add(self, nodes, datasource_uuid, source) -> List[str]:
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

                # Add source and datasource_uuid
                properties["source"] = source
                properties["datasource_uuid"] = datasource_uuid

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

    def create_index(self, schema: Optional[dict]) -> None:
        from weaviate.classes.config import Configure, DataType, Property

        if not self._weaviate_client.collections.exists(self._index_name):
            properties = []
            vectorizer_config = None
            if schema:
                if "properties" in schema:
                    for prop in schema["properties"]:
                        data_type = DataType.TEXT
                        if prop["dataType"][0] == "string[]":
                            data_type = DataType.TEXT_ARRAY
                        properties.append(
                            Property(
                                name=prop["name"],
                                data_type=data_type,
                                description=prop["description"],
                                vectorize_property_name=False,
                            )
                        )

                if "vectorizer" in schema:
                    if schema["vectorizer"] == "text2vec-openai":
                        module_config = schema["moduleConfig"]["text2vec-openai"]
                        module_config.pop("type", None)
                        vectorizer_config = Configure.Vectorizer.text2vec_openai(**module_config)

            return self._weaviate_client.collections.create(
                name=self._index_name,
                vectorizer_config=vectorizer_config,
                properties=properties,
            )

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        nodes = []
        node_ids = []
        similarities = []
        filters = None

        if query.filters:
            filters = _to_weaviate_filter(query.filters)

        if query.mode == VectorStoreQueryMode.HYBRID:
            try:
                query_response = self.client.query.hybrid(
                    query=query.query_str,
                    vector=query.query_embedding,
                    alpha=query.alpha,
                    query_properties=[self._text_key],
                    return_metadata=None,
                    filters=filters,
                )
            except Exception as e:
                raise e

        else:
            try:
                query_response = self.client.query.near_text(
                    query=query.query_str,
                    vector=query.query_embedding,
                    certainty=kwargs.get("search_distance", None),
                    limit=query.similarity_top_k if query.similarity_top_k is not None else 10,
                    return_metadata=wvc.query.MetadataQuery(certainty=True, distance=True),
                    filters=filters,
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
    index_name: Optional[str] = Field(description="Index/Collection name", default=None)
    text_key: str = Field(description="Text key", default="content")
    deployment_name: Optional[str] = Field(description="Deployment name", default="*")
    weaviate_schema: Optional[str] = Field(description="Schema", default="")

    _deployment_config: Optional[WeaviateProviderConfig] = PrivateAttr()
    _schema_dict = PrivateAttr()

    @classmethod
    def slug(cls):
        return "vector-store"

    @classmethod
    def provider_slug(cls):
        return "weaviate"

    def initialize_client(self, *args, **kwargs):
        import weaviate
        from weaviate.connect.helpers import connect_to_custom, connect_to_wcs

        datasource = kwargs.get("datasource")

        index_name = self.index_name or f"Datasource_{datasource.uuid}".replace("-", "_")

        self._deployment_config = datasource.profile.get_provider_config(
            deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )

        DEFAULT_SCHEMA = {
            "class": index_name,
            "description": "Text data source",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {"text2vec-openai": {"model": "ada", "type": "text"}},
            "properties": [
                {
                    "name": self.text_key,
                    "dataType": ["text"],
                    "description": "Text",
                    "moduleConfig": {"text2vec-openai": {"skip": False, "vectorizePropertyName": False}},
                },
                {"name": "source", "dataType": ["text"], "description": "Document source"},
                {"name": "metadata", "dataType": ["string[]"], "description": "Document metadata"},
                {"name": "datasource_uuid", "dataType": ["text"], "description": "Datasource UUID"},
            ],
        }

        try:
            self._schema_dict = json.loads(self.weaviate_schema) if self.weaviate_schema else DEFAULT_SCHEMA
        except Exception:
            pass
        if self._deployment_config and self._deployment_config.module_config:
            self._schema_dict["moduleConfig"] = json.loads(self._deployment_config.module_config)

        additional_headers = self._deployment_config.additional_headers_dict or {}
        if self._deployment_config.embeddings_provider == EmbeddingsProvider.AZURE_OPENAI:
            azure_deployment_config = datasource.profile.get_provider_config(provider_slug="azure")
            additional_headers["X-Azure-Api-Key"] = azure_deployment_config.api_key
        elif self._deployment_config.embeddings_provider == EmbeddingsProvider.OPENAI:
            openai_deployment_config = datasource.profile.get_provider_config(provider_slug="openai")
            additional_headers["X-Openai-Api-Key"] = openai_deployment_config.api_key

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
                host, port = url.split(":") if len(url.split(":")) == 2 else (url, 80)
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
            index_name=index_name,
            text_key=self.text_key,
            auth_config=self._deployment_config.auth,
        )

        # Create collection if it doesn't exist
        self.create_collection()

    def add(self, document: DataDocument) -> DataDocument:
        return self._client.add(document.nodes, datasource_uuid=document.datasource_uuid, source=document.name)

    def delete(self, document: DataDocument) -> DataDocument:
        for node_id in document.node_ids:
            self._client.delete(node_id)

    def search(self, query: str, **kwargs):
        from llama_index.core.vector_stores.types import (
            VectorStoreQuery,
            VectorStoreQueryMode,
        )

        datasource_uuid = kwargs["datasource_uuid"]
        filters = MetadataFilters(filters=[MetadataFilter(key="datasource_uuid", value=datasource_uuid)])

        vector_store_query = VectorStoreQuery(
            query_str=query,
            mode=(
                VectorStoreQueryMode.HYBRID if kwargs.get("use_hybrid_search", False) else VectorStoreQueryMode.DEFAULT
            ),
            alpha=kwargs.get("alpha", 0.75),
            hybrid_top_k=kwargs.get("limit", 2),
            query_embedding=kwargs.get("query_embedding", None),
            filters=filters,
        )

        return self._client.query(query=vector_store_query)

    def create_collection(self):
        return self._client.create_index(schema=self._schema_dict)

    def delete_collection(self):
        if self.index_name != "text":
            self._client.delete_index()

    def get_nodes(self, node_ids: Optional[List[str]] = None, filters: Optional[MetadataFilters] = None):
        return self._client.get_nodes(node_ids=node_ids, filters=filters)
