import json
import logging
from typing import Dict, List, Optional, Union

from pydantic import Field
from typing_extensions import Literal

from llmstack.base.models import Profile
from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.data.store.database.constants import DatabaseEngineType
from llmstack.common.blocks.data.store.database.database_reader import (
    DatabaseReader,
    DatabaseReaderInput,
)
from llmstack.common.blocks.data.store.database.utils import (
    get_database_configuration_class,
)
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.models import Config
from llmstack.connections.models import ConnectionType
from llmstack.datasources.handlers.datasource_processor import (
    DataSourceEntryItem,
    DataSourceProcessor,
    DataSourceSchema,
)
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)


class PostgreSQLConnection(_Schema):
    engine: Literal[DatabaseEngineType.POSTGRESQL] = DatabaseEngineType.POSTGRESQL
    host: str = Field(description="Host of the PostgreSQL instance")
    port: int = Field(
        description="Port number to connect to the PostgreSQL instance",
    )
    database_name: str = Field(description="PostgreSQL database name")

    class Config:
        title = "PostgreSQL"


class MySQLConnection(_Schema):
    engine: Literal[DatabaseEngineType.MYSQL] = DatabaseEngineType.MYSQL
    host: str = Field(description="Host of the MySQL instance")
    port: int = Field(
        description="Port number to connect to the MySQL instance",
    )
    database_name: str = Field(description="MySQL database name")

    class Config:
        title = "MySQL"


class SQLiteConnection(_Schema):
    engine: Literal[DatabaseEngineType.SQLITE] = DatabaseEngineType.SQLITE
    database_path: str = Field(description="SQLite database file path")

    class Config:
        title = "SQLite"


SQLConnection = Union[PostgreSQLConnection, MySQLConnection, SQLiteConnection]


class SQLDatabaseSchema(DataSourceSchema):
    connection: Optional[SQLConnection] = Field(
        default=None,
        title="Database",
        # description="Database details",
    )
    connection_id: Optional[str] = Field(
        default=None,
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
        description="Use your authenticated connection to the database",
        # Filters is a list of strings, each formed by the combination of the connection attributes 'base_connection_type', 'provider_slug', and 'connection_type_slug', separated by '/'.
        # The pattern followed is: base_connection_type/provider_slug/connection_type_slug. We may skip provider_slug or connection_type_slug if they are not present in the filter string.
        filters=[ConnectionType.CREDENTIALS + "/basic_authentication"],
    )


class SQLConnectionConfiguration(Config):
    config_type: Optional[str] = "sql_connection"
    is_encrypted = True
    config: Optional[Dict] = None


class SQLDataSource(DataSourceProcessor[SQLDatabaseSchema]):
    # Initializer for the class.
    # It requires a datasource object as input, checks if it has a 'data'
    # configuration, and sets up Weaviate Database Configuration.
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self.profile = Profile.objects.get(user=self.datasource.owner)
        self._env = self.profile.get_vendor_env()

        if self.datasource.config and "data" in self.datasource.config:
            config_dict = SQLConnectionConfiguration().from_dict(
                self.datasource.config,
                self.datasource.profile.decrypt_value,
            )

            self._configuration = SQLDatabaseSchema(
                **config_dict["config"],
            )

            database_configuration_class = get_database_configuration_class(self._configuration.connection.engine)

            if self._configuration.connection.engine == DatabaseEngineType.SQLITE:
                self._reader_configuration = database_configuration_class(
                    engine=self._configuration.connection.engine,
                    dbpath=self._configuration.connection.database_path,
                )
            else:
                username = password = None

                connection = (
                    self._env["connections"].get(
                        self._configuration.connection_id,
                        None,
                    )
                    if self._configuration.connection_id
                    else None
                )
                if connection and connection["base_connection_type"] == ConnectionType.CREDENTIALS:
                    username = connection["configuration"]["username"]
                    password = connection["configuration"]["password"]

                self._reader_configuration = database_configuration_class(
                    engine=self._configuration.connection.engine,
                    user=username,
                    password=password,
                    host=self._configuration.connection.host,
                    port=self._configuration.connection.port,
                    dbname=self._configuration.connection.database_name,
                    use_ssl=False,
                )
            self._source_name = self.datasource.name

    @staticmethod
    def name() -> str:
        return "SQL"

    @staticmethod
    def slug() -> str:
        return "sql"

    @staticmethod
    def description() -> str:
        return "Connect to a SQL Database"

    # This static method takes a dictionary for configuration and a DataSource object as inputs.
    # Validation of these inputs is performed and a dictionary containing the
    # Database Connection Configuration is returned.
    @staticmethod
    def process_validate_config(
        config_data: dict,
        datasource: DataSource,
    ) -> dict:
        return SQLConnectionConfiguration(
            config=config_data,
        ).to_dict(
            encrypt_fn=datasource.profile.encrypt_value,
        )

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError

    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError

    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        client = DatabaseReader()
        result = (
            client.process(
                DatabaseReaderInput(
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
        client = DatabaseReader()
        result = (
            client.process(
                DatabaseReaderInput(
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
        return None, self._configuration.model_dump_json()
