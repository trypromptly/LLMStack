import json
import logging
from enum import Enum
from string import Template
from typing import List, Optional, TypeVar

from django.conf import settings
from pydantic import BaseModel

from llmstack.base.models import Profile, VectorstoreEmbeddingEndpoint
from llmstack.common.blocks.base.processor import BaseInputType, ProcessorInterface
from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.data.store.vectorstore import (
    Document,
    DocumentQuery,
    VectorStoreInterface,
)
from llmstack.common.blocks.data.store.vectorstore.chroma import Chroma
from llmstack.common.blocks.data.store.vectorstore.weaviate import (
    Weaviate as PromptlyWeaviate,
)
from llmstack.common.blocks.embeddings.openai_embedding import (
    EmbeddingAPIProvider,
    OpenAIEmbeddingConfiguration,
    OpenAIEmbeddingInput,
    OpenAIEmbeddingOutput,
    OpenAIEmbeddingsProcessor,
)
from llmstack.datasources.models import DataSource

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


class DataSourceProcessor(ProcessorInterface[BaseInputType, None, None]):
    @classmethod
    def get_content_key(cls) -> str:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_content_key()

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
    def vectorstore(self) -> VectorStoreInterface:
        return self._vectorstore

    @property
    def embeddings_endpoint(self):
        return self._embeddings_endpoint

    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self.profile = Profile.objects.get(user=self.datasource.owner)
        self._env = self.profile.get_vendor_env()

        vectorstore_embedding_endpoint = self.profile.vectostore_embedding_endpoint
        vectorstore_embeddings_batch_size = self.profile.vectorstore_embeddings_batch_size
        vectorstore_embedding_rate_limit = self.profile.weaviate_embeddings_api_rate_limit

        promptly_weaviate = None
        embedding_endpoint_configuration = None

        default_vector_database = settings.VECTOR_DATABASES.get("default")["ENGINE"]

        if default_vector_database == "weaviate":
            if vectorstore_embedding_endpoint == VectorstoreEmbeddingEndpoint.OPEN_AI:
                promptly_weaviate = PromptlyWeaviate(
                    url=self.profile.weaviate_url,
                    openai_key=self.profile.get_vendor_key("openai_key"),
                    embeddings_rate_limit=vectorstore_embedding_rate_limit,
                    embeddings_batch_size=vectorstore_embeddings_batch_size,
                    api_key=self.profile.weaviate_api_key,
                )
                embedding_endpoint_configuration = OpenAIEmbeddingConfiguration(
                    api_type=EmbeddingAPIProvider.OPENAI,
                    model="text-embedding-ada-002",
                    api_key=self.profile.get_vendor_key("openai_key"),
                )
            else:
                promptly_weaviate = PromptlyWeaviate(
                    url=self.profile.weaviate_url,
                    azure_openai_key=self.profile.get_vendor_key(
                        "azure_openai_api_key",
                    ),
                    weaviate_rw_api_key=self.profile.weaviate_api_key,
                    embeddings_rate_limit=vectorstore_embedding_rate_limit,
                    embeddings_batch_size=vectorstore_embeddings_batch_size,
                )
                embedding_endpoint_configuration = OpenAIEmbeddingConfiguration(
                    api_type=EmbeddingAPIProvider.AZURE_OPENAI,
                    endpoint=self.profile.weaviate_text2vec_config["resourceName"],
                    deploymentId=self.profile.weaviate_text2vec_config["deploymentId"],
                    apiVersion="2022-12-01",
                    api_key=self.profile.get_vendor_key(
                        "azure_openai_api_key",
                    ),
                )

            # Get Weaviate schema
            weaviate_schema = json.loads(
                self.get_weaviate_schema(self.datasource_class_name),
            )
            weaviate_schema["classes"][0]["moduleConfig"]["text2vec-openai"] = self.profile.weaviate_text2vec_config
            weaviate_schema["classes"][0]["replicationConfig"]["factor"] = settings.WEAVIATE_REPLICATION_FACTOR
            weaviate_schema["classes"][0]["shardingConfig"]["desiredCount"] = settings.WEAVIATE_SHARD_COUNT
            # Create an index for the datasource
            promptly_weaviate.get_or_create_index(
                index_name=self.datasource_class_name,
                schema=json.dumps(weaviate_schema),
            )

            self._vectorstore = promptly_weaviate
        elif default_vector_database == "chroma":
            self._vectorstore = Chroma()
            self._vectorstore.get_or_create_index(
                index_name=self.datasource_class_name,
                schema="",
            )

        if self.profile.use_custom_embedding:
            self._embeddings_endpoint = OpenAIEmbeddingsProcessor(
                configuration=embedding_endpoint_configuration.model_dump(),
            )
        else:
            self._embeddings_endpoint = None

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError

    def _get_document_embeddings(self, text: str) -> OpenAIEmbeddingOutput:
        if self.embeddings_endpoint:
            return self.embeddings_endpoint.process(
                OpenAIEmbeddingInput(text=text).model_dump(),
            ).embeddings
        else:
            return None

    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        documents = self.get_data_documents(data)

        documents = map(
            lambda document: Document(
                page_content_key=document.page_content_key,
                page_content=document.page_content,
                metadata={
                    **document.metadata,
                    **data.metadata,
                },
                embeddings=self._get_document_embeddings(
                    document.page_content,
                ),
            ),
            documents,
        )

        document_ids = self.vectorstore.add_texts(
            index_name=self.datasource_class_name,
            documents=documents,
        )
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
        if use_hybrid_search:
            return self.hybrid_search(query, **kwargs)
        else:
            return self.similarity_search(query, **kwargs)

    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        document_query = DocumentQuery(
            query=query,
            page_content_key=self.get_content_key(),
            limit=kwargs.get(
                "limit",
                2,
            ),
            metadata={
                "additional_properties": ["source"],
            },
            search_filters=kwargs.get(
                "search_filters",
                None,
            ),
        )

        return self.vectorstore.similarity_search(
            index_name=self.datasource_class_name,
            document_query=document_query,
            **kwargs,
        )

    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        document_query = DocumentQuery(
            query=query,
            page_content_key=self.get_content_key(),
            limit=kwargs.get(
                "limit",
                2,
            ),
            metadata={
                "additional_properties": ["source"],
            },
            search_filters=kwargs.get(
                "search_filters",
                None,
            ),
            alpha=kwargs.get(
                "alpha",
                0.75,
            ),
        )
        return self.vectorstore.hybrid_search(
            index_name=self.datasource_class_name,
            document_query=document_query,
            **kwargs,
        )

    def delete_entry(self, data: dict) -> None:
        if "document_ids" in data and isinstance(data["document_ids"], list):
            for document_id in data["document_ids"]:
                logger.info(
                    f"Deleting document {document_id} from vectorstore.",
                )
                self.vectorstore.delete_document(
                    document_id,
                    index_name=self.datasource_class_name,
                )

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
        self.vectorstore.delete_index(
            index_name=self.datasource_class_name,
        )

    def get_entry_text(self, data: dict) -> str:
        documents = []
        if "document_ids" in data and isinstance(data["document_ids"], list):
            for document_id in data["document_ids"][:20]:
                content_key = self.get_content_key()
                logger.debug(
                    f"Fetching document {content_key} {self.datasource_class_name} from vectorstore.",
                )
                document = self.vectorstore.get_document_by_id(
                    index_name=self.datasource_class_name,
                    document_id=document_id,
                    content_key=content_key,
                )

                if documents is not None:
                    documents.append(document)

        if len(documents) > 0:
            return documents[0].metadata, "\n".join(
                list(map(lambda x: x.page_content, documents)),
            )
        else:
            return {}, ""
