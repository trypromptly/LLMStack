import json
import logging
from enum import Enum
from string import Template
from typing import List, Optional, TypeVar

from django.conf import settings
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryMode,
)
from pydantic import BaseModel

from llmstack.base.models import Profile
from llmstack.common.blocks.base.processor import BaseInputType, ProcessorInterface
from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.data.destinations.vector_stores.types import (
    get_vector_store_configuration,
)
from llmstack.data.models import DataSource

logger = logging.getLogger(__name__)

EntryConfigurationSchemaType = TypeVar("EntryConfigurationSchemaType")

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


class DataSourceSchema(_Schema):
    """
    This is Base Schema model for all data source type schemas
    """

    @staticmethod
    def get_vector_fields() -> list:
        raise NotImplementedError

    @staticmethod
    def get_content_key() -> str:
        raise NotImplementedError


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


class DataPipeline(ProcessorInterface[BaseInputType, None, None]):
    @classmethod
    def get_content_key(cls) -> str:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_content_key()

    @classmethod
    def is_external(cls) -> bool:
        return False

    @classmethod
    def get_sync_configuration(cls) -> Optional[dict]:
        return None

    @classmethod
    def get_weaviate_schema(cls, class_name: str) -> dict:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_weaviate_schema(class_name)

    @property
    def datasource_class_name(self):
        return "Datasource_" + str(self.datasource.uuid).replace("-", "_")

    @property
    def vectorstore(self) -> BasePydanticVectorStore:
        return self._vectorstore

    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self.profile = Profile.objects.get(user=self.datasource.owner)

        self._vectorstore = self.initialize_vector_datastore()

    def initialize_vector_datastore(self):
        vector_store = None
        vector_data_store_config = self.datasource.vector_store_config
        if not vector_data_store_config:
            raise Exception("Vector store configuration is missing")

        vector_store_config = get_vector_store_configuration(vector_data_store_config)

        # Get Weaviate schema (For Legacy Data Sources)
        legacy_weaviate_schema = json.loads(self.get_weaviate_schema(self.datasource_class_name))
        legacy_weaviate_schema["classes"][0]["moduleConfig"]["text2vec-openai"] = self.profile.weaviate_text2vec_config
        legacy_weaviate_schema["classes"][0]["replicationConfig"]["factor"] = settings.WEAVIATE_REPLICATION_FACTOR
        legacy_weaviate_schema["classes"][0]["shardingConfig"]["desiredCount"] = settings.WEAVIATE_SHARD_COUNT

        vector_store = vector_store_config.initialize_client(
            legacy_weaviate_schema=legacy_weaviate_schema,
            index_name=self.datasource_class_name,
            text_key=self.get_content_key(),
        )
        return vector_store

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError

    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        documents = self.get_data_documents(data)
        documents = list(
            map(
                lambda document: TextNode(text=document.page_content, metadata={**document.metadata, **data.metadata}),
                documents,
            )
        )
        document_ids = self.vectorstore.add(nodes=documents)
        logger.info(f"Added {len(document_ids)} documents to vectorstore.")
        return data.copy(
            update={
                "config": {
                    "document_ids": document_ids,
                },
                "size": 1536 * 4 * len(document_ids),
            },
        )

    def search(
        self,
        query: str,
        use_hybrid_search=True,
        **kwargs,
    ) -> List[dict]:
        if kwargs.get("search_filters", None):
            raise NotImplementedError("Search filters are not supported for this data source.")

        vector_store_query = VectorStoreQuery(
            query_str=query,
            mode=VectorStoreQueryMode.HYBRID if use_hybrid_search else VectorStoreQueryMode.DEFAULT,
            alpha=kwargs.get("alpha", 0.75),
            hybrid_top_k=kwargs.get("limit", 2),
        )
        query_result = self.vectorstore.query(query=vector_store_query)
        documents = list(
            map(
                lambda x: Document(page_content_key=self.get_content_key(), page_content=x.text, metadata={}),
                query_result.nodes,
            )
        )
        return documents

    def delete_entry(self, data: dict) -> None:
        if "document_ids" in data and isinstance(data["document_ids"], list):
            for document_id in data["document_ids"]:
                self.vectorstore.delete(ref_doc_id=document_id)

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
        self.vectorstore.delete_index()

    def get_entry_text(self, data: dict) -> str:
        documents = [TextNode(metadata={}, text="")]

        if "document_ids" in data and isinstance(data["document_ids"], list):
            documents = self.vectorstore.get_nodes(data["document_ids"][:20])

        return documents[0].extra_info, "\n".join(list(map(lambda x: x.text, documents)))
