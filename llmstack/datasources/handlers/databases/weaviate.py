import json
import logging
from typing import Dict, List, Optional

from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.data.store.vectorstore import Document, DocumentQuery
from llmstack.common.blocks.data.store.vectorstore.weaviate import (
    Weaviate,
    WeaviateConfiguration,
)
from llmstack.common.utils.models import Config
from llmstack.datasources.handlers.datasource_processor import (
    DataSourceEntryItem,
    DataSourceProcessor,
    DataSourceSchema,
)
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)

# This is a Python class to establish a connection with Weaviate.
# It accepts the following parameters:
# 1. weaviate_url: URL of the Weaviate instance. It is a mandatory field.
# 2. username: Your username for the Weaviate instance. This is an optional field.
# 3. password: Corresponding password for the above username. This is an optional field.
# 4. api_key: Your Weaviate API key. This is also an optional field.
# 5. additional_headers: Any additional headers that need to be passed in
# the request. This is optional, and should be passed as a JSON string.
# The default value is '{}'.


class WeaviateConnection(_Schema):
    weaviate_url: str = Field(description="Weaviate URL")
    username: Optional[str] = Field(description="Weaviate username")
    password: Optional[str] = Field(description="Weaviate password")
    api_key: Optional[str] = Field(description="Weaviate API key")
    additional_headers: Optional[str] = Field(
        description="Weaviate headers. Please enter a JSON string.",
        widget="textarea",
        default="{}",
    )


# This class is a definition of the Weaviate database schema.
# `index_name`: This is a required string attribute representing the name of the weaviate index.
# `content_property_name`: This is a required string attribute representing the name of the weaviate content property to search.
# `additional_properties`: This is an optional attribute represented as a list of strings.
#                          It's used to specify any additional properties for the Weaviate document,
#                          with 'id' being the default properties.
# `connection`: This is optional and specifies the Weaviate connection string.
# It inherits structure and behaviour from the `DataSourceSchema` class.


class WeaviateDatabaseSchema(DataSourceSchema):
    index_name: str = Field(description="Weaviate index name")
    content_property_name: str = Field(
        description="Weaviate content property name",
    )
    additional_properties: Optional[List[str]] = Field(
        description="Weaviate additional properties",
        default=[],
    )
    connection: Optional[WeaviateConnection] = Field(
        description="Weaviate connection string",
    )


class WeaviateConnectionConfiguration(Config):
    config_type = "weaviate_connection"
    is_encrypted = True
    weaviate_config: Optional[Dict]


# This class helps to manage and interact with a Weaviate Data Source.
# It inherits from the DataSourceProcessor class and operates on a
# WeaviateDatabaseSchema.


class WeaviateDataSource(DataSourceProcessor[WeaviateDatabaseSchema]):
    # Initializer for the class.
    # It requires a datasource object as input, checks if it has a 'data'
    # configuration, and sets up Weaviate Database Configuration.
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        if self.datasource.config and "data" in self.datasource.config:
            config_dict = WeaviateConnectionConfiguration().from_dict(
                self.datasource.config,
                self.datasource.profile.decrypt_value,
            )
            self._configuration = WeaviateDatabaseSchema(
                **config_dict["weaviate_config"],
            )
            self._weviate_client = Weaviate(
                **WeaviateConfiguration(
                    url=self._configuration.connection.weaviate_url,
                    username=self._configuration.connection.username,
                    password=self._configuration.connection.password,
                    api_key=self._configuration.connection.api_key,
                    additional_headers=json.loads(
                        self._configuration.connection.additional_headers,
                    )
                    if self._configuration.connection.additional_headers
                    else {},
                ).dict(),
            )

    # This static method returns the name of the datasource class as
    # 'Weaviate'.
    @staticmethod
    def name() -> str:
        return "Weaviate"

    # This static method returns the slug for the datasource as 'weaviate'.
    @staticmethod
    def slug() -> str:
        return "weaviate"

    @staticmethod
    def description() -> str:
        return "Connect to a Weaviate database"

    # This static method takes a dictionary for configuration and a DataSource object as inputs.
    # Validation of these inputs is performed and a dictionary containing the
    # Weaviate Connection Configuration is returned.
    @staticmethod
    def process_validate_config(
        config_data: dict,
        datasource: DataSource,
    ) -> dict:
        return WeaviateConnectionConfiguration(
            weaviate_config=config_data,
        ).to_dict(
            encrypt_fn=datasource.profile.encrypt_value,
        )

    # This static method returns the provider slug for the datasource
    # connector.
    @staticmethod
    def provider_slug() -> str:
        return "weaviate"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError

    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError

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

    """
    This function performs similarity search on documents by using 'near text' concept of Weaviate where it tries to fetch documents in which concepts match with the given query.
    """

    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        index_name = self._configuration.index_name
        additional_properties = self._configuration.additional_properties

        result = self._weviate_client.similarity_search(
            index_name=index_name,
            document_query=DocumentQuery(
                query=query,
                page_content_key=self._configuration.content_property_name,
                limit=kwargs.get("limit", 2),
                metadata={
                    "additional_properties": additional_properties,
                    "metadata_properties": ["distance"],
                },
                search_filters=kwargs.get("search_filters", None),
            ),
            **kwargs,
        )
        return result

    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        index_name = self._configuration.index_name
        additional_properties = self._configuration.additional_properties
        result = self._weviate_client.hybrid_search(
            index_name=index_name,
            document_query=DocumentQuery(
                alpha=kwargs.get("alpha", 0.75),
                query=query,
                page_content_key=self._configuration.content_property_name,
                limit=kwargs.get("limit", 2),
                metadata={
                    "additional_properties": additional_properties,
                    "metadata_properties": ["score"],
                },
                search_filters=kwargs.get("search_filters", None),
            ),
            **kwargs,
        )
        return result

    def delete_entry(self, data: dict) -> None:
        raise NotImplementedError

    def resync_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError

    def delete_all_entries(self) -> None:
        raise NotImplementedError

    def get_entry_text(self, data: dict) -> str:
        return None, self._configuration.json()
