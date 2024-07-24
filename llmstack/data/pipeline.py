import logging
from typing import List, Optional

from llama_index.core.schema import TextNode

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.data.models import DataSource
from llmstack.data.schemas import DataDocument
from llmstack.data.sources.base import BaseSource

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self._source_cls = self.datasource.pipeline_obj.source_cls
        self._destination_cls = self.datasource.pipeline_obj.destination_cls

        self._destination = None

        if self._destination_cls:
            self._destination = self._destination_cls(**self.datasource.destination_data)
            self._destination.initialize_client(datasource=self.datasource)

    def add_data(self, source_data_dict={}):
        source: Optional[BaseSource] = None
        documents: List[DataDocument] = []

        if self._source_cls:
            source = self._source_cls(**source_data_dict)

        if source:
            documents = source.get_data_documents(datasource_uuid=str(self.datasource.uuid))
            documents = list(map(lambda d: source.process_document(d), documents))

        for document in documents:
            if self.datasource.type_slug == "csv":
                text_splits = CSVTextSplitter(
                    chunk_size=2, length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken
                ).split_text(document.text)
            else:
                text_splits = SpacyTextSplitter(chunk_size=1500).split_text(document.text)
            document.nodes = list(map(lambda t: TextNode(text=t, metadata={**document.metadata}), text_splits))

        if self._destination:
            for document in documents:
                self._destination.add(document=document)

        return documents

    def delete_entry(self, data: dict) -> None:
        node_ids = data.get("document_ids", [])
        if not node_ids:
            node_ids = data.get("nodes", [])

        data_document = DataDocument()
        data_document.nodes = list(map(lambda x: TextNode(id_=x), node_ids))
        if self._destination:
            self._destination.delete(document=data_document)

    def resync_entry(self, data: dict):
        raise NotImplementedError

    def delete_all_entries(self) -> None:
        if self._destination:
            self._destination.delete_collection()


class DataQueryPipeline:
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self._destination_cls = self.datasource.destination_cls
        self._destination = None

        if self._destination_cls:
            self._destination = self._destination_cls(**self.datasource.destination_data)
            self._destination.initialize_client(datasource=self.datasource)

    def search(self, query: str, use_hybrid_search=True, **kwargs) -> List[dict]:
        content_key = self.datasource.destination_text_content_key

        if kwargs.get("search_filters", None):
            raise NotImplementedError("Search filters are not supported for this data source.")

        documents = []

        if self._destination:
            query_result = self._destination.search(query=query, use_hybrid_search=use_hybrid_search, **kwargs)
            documents = list(
                map(
                    lambda x: Document(page_content_key=content_key, page_content=x.text, metadata=x.metadata),
                    query_result.nodes,
                )
            )
        return documents

    def get_entry_text(self, data: dict) -> str:
        documents = [TextNode(metadata={}, text="")]
        node_ids = data.get("document_ids", [])
        if not node_ids:
            node_ids = data.get("nodes", [])

        if self._destination:
            self._destination.initialize_client(datasource=self.datasource)
            if node_ids:
                result = self._destination.get_nodes(node_ids[:20])
                if result:
                    documents = result
        return documents[0].extra_info, "\n".join(list(map(lambda x: x.text, documents)))
