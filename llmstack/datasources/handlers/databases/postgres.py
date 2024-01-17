import json
import logging
from typing import Dict, List, Optional

from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.data.store.postgres import PostgresConfiguration
from llmstack.common.blocks.data.store.postgres.read import (
    PostgresReader,
    PostgresReaderInput,
)
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.models import Config
from llmstack.datasources.handlers.datasource_processor import (
    DataSourceEntryItem,
    DataSourceProcessor,
    DataSourceSchema,
)
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)


class PostgresConnection(_Schema):
    host: str = Field(description="Host of the Postgres instance")
    port: int = Field(
        description="Port number to connect to the Postgres instance",
    )
    database_name: str = Field(description="Postgres database name")
    username: str = Field(description="Postgres username")
    password: Optional[str] = Field(description="Postgres password")


class PostgresDatabaseSchema(DataSourceSchema):
    connection: Optional[PostgresConnection] = Field(
        description="Postgres connection details",
    )


class PostgresConnectionConfiguration(Config):
    config_type = "postgres_connection"
    is_encrypted = True
    postgres_config: Optional[Dict]


class PostgresDataSource(DataSourceProcessor[PostgresDatabaseSchema]):
    # Initializer for the class.
    # It requires a datasource object as input, checks if it has a 'data'
    # configuration, and sets up Weaviate Database Configuration.
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        if self.datasource.config and "data" in self.datasource.config:
            config_dict = PostgresConnectionConfiguration().from_dict(
                self.datasource.config,
                self.datasource.profile.decrypt_value,
            )
            self._configuration = PostgresDatabaseSchema(
                **config_dict["postgres_config"],
            )
            self._reader_configuration = PostgresConfiguration(
                user=self._configuration.connection.username,
                password=self._configuration.connection.password,
                host=self._configuration.connection.host,
                port=self._configuration.connection.port,
                dbname=self._configuration.connection.database_name,
                use_ssl=False,
            )
            self._source_name = self.datasource.name

    @staticmethod
    def name() -> str:
        return "Postgres"

    @staticmethod
    def slug() -> str:
        return "postgres"

    @staticmethod
    def description() -> str:
        return "Connect to a Postgres database"

    # This static method takes a dictionary for configuration and a DataSource object as inputs.
    # Validation of these inputs is performed and a dictionary containing the
    # Postgres Connection Configuration is returned.
    @staticmethod
    def process_validate_config(
        config_data: dict,
        datasource: DataSource,
    ) -> dict:
        return PostgresConnectionConfiguration(
            postgres_config=config_data,
        ).to_dict(
            encrypt_fn=datasource.profile.encrypt_value,
        )

    # This static method returns the provider slug for the datasource
    # connector.
    @staticmethod
    def provider_slug() -> str:
        return "postgres"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError

    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError

    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        pg_client = PostgresReader()
        result = (
            pg_client.process(
                PostgresReaderInput(
                    sql=query,
                ),
                configuration=self._reader_configuration,
            )
            .documents[0]
            .content_text
        )
        json_result = json.loads(result)
        # JSON to csv
        csv_result = ""
        for row in json_result["rows"]:
            csv_result += (
                ",".join(
                    list(
                        map(
                            lambda entry: str(entry),
                            row.values(),
                        ),
                    ),
                )
                + "\n"
            )
        return [
            Document(
                page_content_key="content",
                page_content=csv_result,
                metadata={
                    "score": 0,
                    "source": self._source_name,
                },
            ),
        ]

    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        pg_client = PostgresReader()
        result = (
            pg_client.process(
                PostgresReaderInput(
                    sql=query,
                ),
                configuration=self._reader_configuration,
            )
            .documents[0]
            .content_text
        )
        json_result = json.loads(result)
        # JSON to csv
        csv_result = ""
        for row in json_result["rows"]:
            csv_result += (
                ",".join(
                    list(
                        map(
                            lambda entry: str(entry),
                            row.values(),
                        ),
                    ),
                )
                + "\n"
            )

        return [
            Document(
                page_content_key="content",
                page_content=csv_result,
                metadata={
                    "score": 0,
                    "source": self._source_name,
                },
            ),
        ]

    def delete_entry(self, data: dict) -> None:
        raise NotImplementedError

    def resync_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError

    def delete_all_entries(self) -> None:
        raise NotImplementedError

    def get_entry_text(self, data: dict) -> str:
        return None, self._configuration.json()
