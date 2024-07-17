import logging
from typing import List, Optional

from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode

from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.data.models import DataSource
from llmstack.data.sources.base import BaseSource

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
        results = []
        source: Optional[BaseSource] = None

        if self._source_cls:
            source = self._source_cls(**source_data_dict)

        if source:
            documents: List[DataDocument] = source.get_data_documents()
            for document in documents:
                nodes = []
                text_splits = []
                process_result = {
                    "name": document.name,
                    "document_data": document.model_dump(),
                    "dataprocessed_size": 0,
                    "metadata": document.metadata,
                    "source_data": source.model_dump(),
                }

                if self.datasource.type_slug == "csv":
                    text_splits = CSVTextSplitter(
                        chunk_size=2, length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken
                    ).split_text(document.content_text)
                else:
                    text_splits = SpacyTextSplitter(chunk_size=1500).split_text(document.content_text)

                nodes = list(map(lambda t: TextNode(text=t, metadata={**document.metadata}), text_splits))
                if self._destination:
                    destination_client = self._destination.initialize_client()
                    document_ids = destination_client.add(nodes=nodes)
                    process_result["dataprocessed_size"] = 1536 * 4 * len(document_ids)
                    process_result["document_ids"] = document_ids

                results.append(process_result)

        return results

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
