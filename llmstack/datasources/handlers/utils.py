import logging
from typing import Any, Dict, List, Optional, cast

import weaviate
import weaviate.classes as wvc
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)
from llama_index.core.vector_stores.utils import DEFAULT_TEXT_KEY
from llama_index.vector_stores.weaviate.base import _to_weaviate_filter
from llama_index.vector_stores.weaviate.utils import (
    add_node,
    class_schema_exists,
    get_all_properties,
    get_node_similarity,
    parse_get_response,
    to_node,
)
from pydantic import Field, PrivateAttr

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.common.utils.text_extract import extract_text_elements

_logger = logging.getLogger(__name__)


def extract_documents(
    file_data,
    content_key,
    mime_type,
    file_name,
    metadata,
    chunk_size=1500,
):
    docs = []
    elements = extract_text_elements(
        mime_type=mime_type,
        data=file_data,
        file_name=file_name,
    )
    file_content = "\n\n".join([str(el) for el in elements])

    if mime_type == "text/csv":
        docs = [
            Document(
                page_content_key=content_key,
                page_content=t,
                metadata=metadata,
            )
            for t in CSVTextSplitter(
                chunk_size=chunk_size,
                length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
            ).split_text(file_content)
        ]
    else:
        docs = [
            Document(
                page_content_key=content_key,
                page_content=t,
                metadata=metadata,
            )
            for t in SpacyTextSplitter(
                chunk_size=chunk_size,
            ).split_text(file_content)
        ]
    return docs


class PromptlyWeaviateVectorStore(BasePydanticVectorStore):
    """Promptly Weaviate vector store.


    Args:
        weaviate_client (weaviate.Client): WeaviateClient
            instance from `weaviate-client` package
        index_name (Optional[str]): name for Weaviate classes

    Examples:
        `pip install llama-index-vector-stores-weaviate`

        ```python
        import weaviate

        resource_owner_config = weaviate.AuthClientPassword(
            username="<username>",
            password="<password>",
        )
        client = weaviate.Client(
            "https://llama-test-ezjahb4m.weaviate.network",
            auth_client_secret=resource_owner_config,
        )

        vector_store = WeaviateVectorStore(
            weaviate_client=client, index_name="LlamaIndex"
        )
        ```
    """

    stores_text: bool = True

    index_name: str
    url: Optional[str]
    text_key: str
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    client_kwargs: Dict[str, Any] = Field(default_factory=dict)

    _client = PrivateAttr()

    def __init__(
        self,
        weaviate_client: Optional[Any] = None,
        class_prefix: Optional[str] = None,
        index_name: Optional[str] = None,
        text_key: str = "text",
        auth_config: Optional[Any] = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        if weaviate_client is None:
            raise ValueError("weaviate_client is required")
        else:
            self._client = cast(weaviate.WeaviateClient, weaviate_client)

        if not index_name:
            raise ValueError("index_name is required")

        if not index_name[0].isupper():
            raise ValueError("Index name must start with a capital letter")

        # create default schema if does not exist
        if not class_schema_exists(self._client, index_name):
            raise ValueError(f"Index '{index_name}' does not exist. Please create it first.")

        super().__init__(
            url=url,
            index_name=index_name,
            text_key=text_key,
            auth_config=auth_config.__dict__ if auth_config else {},
            client_kwargs=client_kwargs or {},
        )

    @classmethod
    def from_params(
        cls,
        url: str,
        auth_config: Any,
        index_name: Optional[str] = None,
        text_key: str = DEFAULT_TEXT_KEY,
        client_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Create WeaviateVectorStore from config."""
        client_kwargs = client_kwargs or {}
        weaviate_client = weaviate.Client(url=url, auth_client_secret=auth_config, **client_kwargs)
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
        return "PromptlyWeaviateVectorStore"

    @property
    def client(self) -> Any:
        """Get client."""
        return self._client

    def add(
        self,
        nodes,
        **add_kwargs: Any,
    ) -> List[str]:
        """Add nodes to index.

        Args:
            nodes: List[BaseNode]: list of nodes with embeddings

        """
        ids = [r.node_id for r in nodes]

        with self._client.batch.dynamic() as batch:
            for node in nodes:
                add_node(
                    self._client,
                    node,
                    self.index_name,
                    batch=batch,
                    text_key=self.text_key,
                )
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """
        Delete nodes using with ref_doc_id.

        Args:
            ref_doc_id (str): The doc_id of the document to delete.

        """
        where_filter = {
            "path": ["ref_doc_id"],
            "operator": "Equal",
            "valueText": ref_doc_id,
        }
        if "filter" in delete_kwargs and delete_kwargs["filter"] is not None:
            where_filter = {
                "operator": "And",
                "operands": [where_filter, delete_kwargs["filter"]],  # type: ignore
            }

        query = (
            self._client.query.get(self.index_name)
            .with_additional(["id"])
            .with_where(where_filter)
            .with_limit(10000)  # 10,000 is the max weaviate can fetch
        )

        query_result = query.do()
        parsed_result = parse_get_response(query_result)
        entries = parsed_result[self.index_name]
        for entry in entries:
            self._client.data_object.delete(entry["_additional"]["id"], self.index_name)

    def delete_index(self) -> None:
        """Delete the index associated with the client.

        Raises:
        - Exception: If the deletion fails, for some reason.
        """
        if not class_schema_exists(self._client, self.index_name):
            _logger.warning(f"Index '{self.index_name}' does not exist. No action taken.")
            return
        try:
            self._client.collections.delete(self.index_name)
            _logger.info(f"Successfully deleted index '{self.index_name}'.")
        except Exception as e:
            _logger.error(f"Failed to delete index '{self.index_name}': {e}")
            raise Exception(f"Failed to delete index '{self.index_name}': {e}")

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """Query index for top k most similar nodes."""
        all_properties = get_all_properties(self._client, self.index_name)
        collection = self._client.collections.get(self.index_name)
        filters = None

        # list of documents to constrain search
        if query.doc_ids:
            filters = wvc.query.Filter.by_property("doc_id").contains_any(query.doc_ids)

        if query.node_ids:
            filters = wvc.query.Filter.by_property("id").contains_any(query.node_ids)

        return_metatada = wvc.query.MetadataQuery(distance=True, score=True)

        vector = query.query_embedding
        similarity_key = "distance"
        if query.mode == VectorStoreQueryMode.DEFAULT:
            _logger.debug("Using vector search")
            if vector is not None:
                alpha = 1
        elif query.mode == VectorStoreQueryMode.HYBRID:
            _logger.debug(f"Using hybrid search with alpha {query.alpha}")
            similarity_key = "score"
            if vector is not None and query.query_str:
                alpha = query.alpha

        if query.filters is not None:
            filters = _to_weaviate_filter(query.filters)
        elif "filter" in kwargs and kwargs["filter"] is not None:
            filters = kwargs["filter"]

        limit = query.similarity_top_k
        _logger.debug(f"Using limit of {query.similarity_top_k}")

        # execute query
        try:
            query_result = collection.query.hybrid(
                query=query.query_str,
                vector=vector,
                alpha=alpha,
                limit=limit,
                filters=filters,
                return_metadata=return_metatada,
                return_properties=all_properties,
                include_vector=True,
            )
        except weaviate.exceptions.WeaviateQueryError as e:
            raise ValueError(f"Invalid query, got errors: {e.message}")

        # parse results

        entries = query_result.objects

        similarities = []
        nodes = []
        node_ids = []

        for i, entry in enumerate(entries):
            if i < query.similarity_top_k:
                entry_as_dict = entry.__dict__
                similarities.append(get_node_similarity(entry_as_dict, similarity_key))
                nodes.append(to_node(entry_as_dict, text_key=self.text_key))
                node_ids.append(nodes[-1].node_id)
            else:
                break

        return VectorStoreQueryResult(nodes=nodes, ids=node_ids, similarities=similarities)
