import logging
from typing import List

from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.data.models import DataSource

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self.profile = datasource.profile
        self._source_cls = self.datasource.source_cls
        self._destination_cls = self.datasource.destination_cls
        self._transformation_cls = self.datasource.transformation_cls

        self._destination = None
        self._transformation = None

        if self._destination_cls:
            self._destination = self._destination_cls(**self.datasource.destination_data)

        if self._transformation_cls:
            self._transformation = self._transformation_cls(**self.datasource.transformation_data)

    def run(self, source_data_dict={}):
        source = None

        if self._source_cls:
            source = self._source_cls(**source_data_dict)

        result = {
            "name": source.name or source.display_name(),
            "source_data": source.model_dump(),
            "dataprocessed_size": 0,
            "metadata": {},
            "status_code": 200,
            "detail": "Success",
        }

        nodes = []
        try:
            if source:
                # Get data from the source
                documents = source.get_data_documents()
                nodes = list(
                    map(
                        lambda document: TextNode(text=document.page_content, metadata={**document.metadata}),
                        documents,
                    )
                )
            if self._destination:
                destination_client = self._destination.initialize_client()
                # Ids of the documents added to the destination
                document_ids = destination_client.add(nodes=nodes)
                result["dataprocessed_size"] = 1536 * 4 * len(document_ids)
                result["metadata"]["destination"] = {"document_ids": document_ids, "size": 1536 * 4 * len(document_ids)}
        except Exception as e:
            result["status_code"] = 500
            result["detail"] = str(e)

        return result

    def search(self, query: str, use_hybrid_search=True, **kwargs) -> List[dict]:
        content_key = self.datasource.destination_text_content_key

        if kwargs.get("search_filters", None):
            raise NotImplementedError("Search filters are not supported for this data source.")

        documents = []

        if self._destination:
            destination_client = self._destination.initialize_client()

            vector_store_query = VectorStoreQuery(
                query_str=query,
                mode=VectorStoreQueryMode.HYBRID if use_hybrid_search else VectorStoreQueryMode.DEFAULT,
                alpha=kwargs.get("alpha", 0.75),
                hybrid_top_k=kwargs.get("limit", 2),
            )
            query_result = destination_client.query(query=vector_store_query)
            documents = list(
                map(
                    lambda x: Document(page_content_key=content_key, page_content=x.text, metadata=x.metadata),
                    query_result.nodes,
                )
            )
        return documents

    def delete_entry(self, data: dict) -> None:
        if self._destination:
            destination_client = self._destination.initialize_client()
            if "document_ids" in data and isinstance(data["document_ids"], list):
                for document_id in data["document_ids"]:
                    destination_client.delete(ref_doc_id=document_id)

    def resync_entry(self, data: dict):
        raise NotImplementedError

    def delete_all_entries(self) -> None:
        if self._destination:
            destination_client = self._destination.initialize_client()
            destination_client.delete_index()

    def get_entry_text(self, data: dict) -> str:
        documents = [TextNode(metadata={}, text="")]

        if self._destination:
            destination_client = self._destination.initialize_client()
            if "document_ids" in data and isinstance(data["document_ids"], list):
                result = destination_client.get_nodes(data["document_ids"][:20])
                if result:
                    documents = result
        return documents[0].extra_info, "\n".join(list(map(lambda x: x.text, documents)))
