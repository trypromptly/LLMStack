import logging
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

import weaviate
import weaviate.classes as wvc
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)
from llama_index.core.vector_stores.utils import (
    DEFAULT_TEXT_KEY,
    legacy_metadata_dict_to_node,
    metadata_dict_to_node,
)
from weaviate import Client

from llmstack.datasources.vector_stores.base import VectorStoreConfiguration

_logger = logging.getLogger(__name__)


def _transform_weaviate_filter_condition(condition: str) -> str:
    """Translate standard metadata filter op to Chroma specific spec."""
    if condition == "and":
        return wvc.query.Filter.all_of
    elif condition == "or":
        return wvc.query.Filter.any_of
    else:
        raise ValueError(f"Filter condition {condition} not supported")


def _transform_weaviate_filter_operator(operator: str) -> str:
    """Translate standard metadata filter operator to Weaviate specific spec."""
    if operator == "!=":
        return "not_equal"
    elif operator == "==":
        return "equal"
    elif operator == ">":
        return "greater_than"
    elif operator == "<":
        return "less_than"
    elif operator == ">=":
        return "greater_or_equal"
    elif operator == "<=":
        return "less_or_equal"
    else:
        raise ValueError(f"Filter operator {operator} not supported")


def _to_weaviate_filter(
    standard_filters: MetadataFilters,
) -> Union[wvc.query.Filter, List[wvc.query.Filter]]:
    filters_list = []
    condition = standard_filters.condition or "and"
    condition = _transform_weaviate_filter_condition(condition)

    if standard_filters.filters:
        for filter in standard_filters.filters:
            filters_list.append(
                getattr(
                    wvc.query.Filter.by_property(filter.key),
                    _transform_weaviate_filter_operator(filter.operator),
                )(filter.value)
            )
    else:
        return {}

    if len(filters_list) == 1:
        # If there is only one filter, return it directly
        return filters_list[0]

    return condition(filters_list)


def to_node(entry: Dict, text_key: str = DEFAULT_TEXT_KEY) -> TextNode:
    """Convert to Node."""
    text = entry.pop(text_key, "")

    try:
        node = metadata_dict_to_node(entry["metadata"])
        node.text = text
        node.embedding = None
    except Exception as e:
        _logger.debug("Failed to parse Node metadata, fallback to legacy logic. %s", e)
        metadata, node_info, relationships = legacy_metadata_dict_to_node(entry)

        node = TextNode(
            text=text,
            id_=entry.get("_additional", {}).get("id", str(uuid4())),
            metadata=metadata,
            start_char_idx=node_info.get("start", None),
            end_char_idx=node_info.get("end", None),
            relationships=relationships,
            embedding=None,
        )
    return node


class PromptlyLegacyWeaviateVectorStore(BasePydanticVectorStore):
    """Promptly Legacy Weaviate vector store."""

    stores_text: bool = True
    _client = PrivateAttr()
    _index_name = PrivateAttr()
    _text_key = PrivateAttr()

    def __init__(
        self,
        weaviate_client: Optional[Any] = None,
        class_prefix: Optional[str] = None,
        index_name: Optional[str] = None,
        text_key: str = DEFAULT_TEXT_KEY,
        auth_config: Optional[Any] = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        self._client: weaviate.Client = weaviate_client

        if not index_name:
            raise ValueError("Index name must be provided")
        self._index_name = index_name

        if not index_name[0].isupper():
            raise ValueError("Index name must start with a capital letter, e.g. 'LlamaIndex'")

        # create default schema if does not exist
        # Check if schema exists
        try:
            self._client.schema.get(index_name)
        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            if e.status_code == 404:
                pass
                # self.create_index(kwargs.get("index_schema", {}))

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
    def from_params(
        cls,
        url: str,
        auth_config: Any,
        index_name: Optional[str] = None,
        text_key: str = DEFAULT_TEXT_KEY,
        client_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "PromptlyLegacyWeaviateVectorStore":
        """Create PromptlyLegacyWeaviateVectorStore from config."""
        client_kwargs = client_kwargs or {}
        weaviate_client = Client(url=url, auth_client_secret=auth_config, **client_kwargs)
        return cls(
            weaviate_client=weaviate_client,
            url=url,
            auth_config=auth_config.__dict__,
            client_kwargs=client_kwargs,
            index_name=index_name,
            text_key=text_key,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        return "PromptlyLegacyWeaviateVectorStore"

    def get_nodes(
        self,
        node_ids: Optional[List[str]] = None,
        filters: Optional[MetadataFilters] = None,
    ) -> List[BaseNode]:
        result = []
        for node_id in node_ids:
            try:
                object_data = self.client.data_object.get_by_id(node_id, class_name=self._index_name)
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
                _logger.error("Error in similarity search: %s" % e)
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


class PromptlyLegacyWeaviateVectorStoreConfiguration(VectorStoreConfiguration):
    type: Literal["promptly_legacy_weaviate"] = "promptly_legacy_weaviate"
    url: str
    host: Optional[str] = None
    http_port: Optional[int] = None
    grpc_port: Optional[int] = None
    embeddings_rate_limit: Optional[int] = None
    embeddings_batch_size: Optional[int] = None
    additional_headers: Optional[dict] = None
    api_key: Optional[str] = None

    def initialize_client(self, *args, **kwargs) -> BasePydanticVectorStore:
        weaviate_schema = kwargs.get("legacy_weaviate_schema", {})
        weaviate_client = weaviate.Client(
            url=self.url,
            additional_headers=self.additional_headers,
            auth_client_secret=weaviate.auth.AuthApiKey(api_key=self.api_key),
        )

        return PromptlyLegacyWeaviateVectorStore(
            weaviate_client=weaviate_client,
            text_key=kwargs.get("text_key", DEFAULT_TEXT_KEY),
            index_name=kwargs.get("index_name", "text"),
            index_schema=weaviate_schema,
        )
