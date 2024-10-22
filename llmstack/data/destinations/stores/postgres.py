import logging
from typing import Any, Dict, Optional

import sqlalchemy
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult
from pydantic import Field, PrivateAttr

from llmstack.common.api_client_internal import get_connections
from llmstack.data.destinations.base import BaseDestination

logger = logging.getLogger(__name__)


def fetch_columns(columns):
    import collections

    column_names = set()
    duplicates_counters = collections.defaultdict(int)
    new_columns = []

    for col in columns:
        column_name = col[0]
        while column_name in column_names:
            duplicates_counters[col[0]] += 1
            column_name = "{}{}".format(
                col[0],
                duplicates_counters[col[0]],
            )

        column_names.add(column_name)
        new_columns.append({"name": column_name, "type": col[1]})

    return new_columns


def get_database_connection(
    conn_configuration: dict,
    database_name: str = None,
    database_host: str = None,
    database_port: int = None,
):
    import sqlalchemy

    # Create URL
    db_url = sqlalchemy.engine.URL.create(
        drivername="postgresql",
        username=conn_configuration.get("username").strip(),
        password=conn_configuration.get("password").strip(),
        host=database_host,
        port=database_port,
        database=database_name,
    )

    # Create engine
    engine = sqlalchemy.create_engine(db_url)

    # Connect to the database
    connection = engine.connect()

    return connection


class PostgresDatabase(BaseDestination):
    database: str = Field(description="Database name")
    host: str = Field(description="Host")
    port: int = Field(description="Port")
    connection_id: Optional[str] = Field(
        default=None,
        description="Connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    _connection_config: Optional[Dict[str, Any]] = PrivateAttr()

    @classmethod
    def slug(cls):
        return "postgres"

    @classmethod
    def provider_slug(cls):
        return "postgres"

    def initialize_client(self, *args, **kwargs):
        datasource = kwargs.get("datasource")
        connections = get_connections(datasource.profile)
        if self.connection_id:
            self._connection_config = connections[self.connection_id]

    def search(self, query: str, **kwargs):
        connection = get_database_connection(
            conn_configuration=self._connection_config.get("configuration", {}),
            database_name=self.database,
            database_host=self.host,
            database_port=self.port,
        )
        result = connection.execute(sqlalchemy.text(query))
        cursor = result.cursor
        csv_text = ""
        if cursor.description is not None:
            columns = fetch_columns(
                [(i[0], None) for i in cursor.description],
            )
            rows = [dict(zip((column["name"] for column in columns), row)) for row in cursor]
            # Convert to CSV
            csv_text = ",".join([column["name"] for column in columns]) + "\n"
            for row in rows:
                csv_text += ",".join([str(row.get(column["name"], "")) for column in columns]) + "\n"

        return VectorStoreQueryResult(
            nodes=[TextNode(text=csv_text, metadata={"query": query, "source": self.database})]
        )
