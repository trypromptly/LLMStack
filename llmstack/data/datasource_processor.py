import logging
from enum import Enum
from typing import List, Optional

from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode
from pydantic import BaseModel

from llmstack.base.models import Profile
from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.data.models import DataSource
from llmstack.data.sources.utils import get_destination_cls, get_source_cls

logger = logging.getLogger(__name__)


class DataSourceEntryItem(BaseModel):
    """
    This is the response model for a single data source entry
    """

    uuid: str = ""
    name: str = ""
    config: dict = {}
    size: int = 0
    metadata: dict = {}
    data: Optional[dict] = None


class DataSourceSyncType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class DataSourceSyncConfiguration(_Schema):
    sync_type: DataSourceSyncType = "full"


class DataPipeline:
    def __init__(self, datasource: DataSource, source_data={}, destination_data={}, transformations_data=[]):
        self.datasource = datasource
        self.profile = Profile.objects.get(user=self.datasource.owner)
        self._pipeline_source_cls = self._get_source_cls()
        self._pipeline_source_obj = self._pipeline_source_cls(**source_data) if self._pipeline_source_cls else None

        self._pipeline_destination_cls = self._get_destination_cls()
        self._pipeline_destination_obj = (
            self._pipeline_destination_cls(**destination_data) if self._pipeline_destination_cls else None
        )

    @property
    def source_data(self):
        return self._pipeline_source_obj.model_dump() if self._pipeline_source_obj else {}

    @property
    def destination_data(self):
        return self._pipeline_destination_obj.model_dump() if self._pipeline_destination_obj else {}

    def _get_source_cls(self):
        source_cls = None
        source_config = self.datasource.source_config
        if source_config:
            source_cls = get_source_cls(source_config.slug, source_config.provider_slug)

        return source_cls

    def _get_destination_cls(self):
        destination_cls = None
        destination_config = self.datasource.destination_config
        if destination_config:
            destination_cls = get_destination_cls(destination_config.slug, destination_config.provider_slug)

        return destination_cls

    def run_name(self):
        return self._pipeline_source_obj.name or self._pipeline_source_obj.display_name()

    def run(self):
        result = {
            "name": self.run_name(),
            "source_data": self.source_data,
            "destination_data": self.destination_data,
            "transformations_data": [],
            "dataprocessed_size": 0,
            "metadata": {},
            "status_code": 200,
            "detail": "Success",
        }

        nodes = []
        try:
            if self._pipeline_source_obj:
                # Get data from the source
                documents = self._pipeline_source_obj.get_data_documents()

                nodes = list(
                    map(
                        lambda document: TextNode(text=document.page_content, metadata={**document.metadata}),
                        documents,
                    )
                )

            if self._pipeline_destination_obj:
                destination_client = self._pipeline_destination_obj.initialize_client()
                # Ids of the documents added to the destination
                document_ids = destination_client.add(nodes=nodes)

                result["dataprocessed_size"] = 1536 * 4 * len(document_ids)

                result["metadata"]["destination"] = {"document_ids": document_ids, "size": 1536 * 4 * len(document_ids)}
        except Exception as e:
            result["status_code"] = 500
            result["detail"] = str(e)

        return result

    def search(
        self,
        query: str,
        use_hybrid_search=True,
        **kwargs,
    ) -> List[dict]:
        if kwargs.get("search_filters", None):
            raise NotImplementedError("Search filters are not supported for this data source.")

        documents = []

        if self._pipeline_destination_obj:
            destination_client = self._pipeline_destination_obj.initialize_client()

            vector_store_query = VectorStoreQuery(
                query_str=query,
                mode=VectorStoreQueryMode.HYBRID if use_hybrid_search else VectorStoreQueryMode.DEFAULT,
                alpha=kwargs.get("alpha", 0.75),
                hybrid_top_k=kwargs.get("limit", 2),
            )
            query_result = destination_client.query(query=vector_store_query)
            documents = list(
                map(
                    lambda x: Document(page_content_key=self.get_content_key(), page_content=x.text, metadata={}),
                    query_result.nodes,
                )
            )
        return documents

    def delete_entry(self, data: dict) -> None:
        if self._pipeline_destination_obj:
            destination_client = self._pipeline_destination_obj.initialize_client()
            if "document_ids" in data and isinstance(data["document_ids"], list):
                for document_id in data["document_ids"]:
                    destination_client.delete(ref_doc_id=document_id)

    def resync_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        # Delete old data
        try:
            self.delete_entry(data)
        except Exception as e:
            logger.error(
                f"Error while deleting old data for data_source_entry: {data} - {e}",
            )
        # Add new data
        return self.add_entry(DataSourceEntryItem(**data["input"]))

    def delete_all_entries(self) -> None:
        if self._pipeline_destination_obj:
            destination_client = self._pipeline_destination_obj.initialize_client()
            destination_client.delete_index()

    def get_entry_text(self, data: dict) -> str:
        documents = [TextNode(metadata={}, text="")]

        if self._pipeline_destination_obj:
            destination_client = self._pipeline_destination_obj.initialize_client()
            if "document_ids" in data and isinstance(data["document_ids"], list):
                result = destination_client.get_nodes(data["document_ids"][:20])
                if result:
                    documents = result

        return documents[0].extra_info, "\n".join(list(map(lambda x: x.text, documents)))
