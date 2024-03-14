from enum import StrEnum
from typing import List

import sqlalchemy

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.database.mysql import (
    MySQLConfiguration,
    get_mysql_ssl_config,
)
from llmstack.common.blocks.data.store.database.postgresql import (
    PostgresConfiguration,
    get_pg_ssl_config,
)
from llmstack.common.blocks.data.store.database.sqlite import SQLiteConfiguration


class DatabaseEngineType(StrEnum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


DATABASES = {
    DatabaseEngineType.POSTGRESQL: {
        "name": "PostgreSQL",
        "driver": "postgresql+psycopg2",
    },
    DatabaseEngineType.MYSQL: {
        "name": "MySQL",
        "driver": "mysql+mysqldb",
    },
    DatabaseEngineType.SQLITE: {
        "name": "SQLite",
        "driver": "sqlite+pysqlite",
    },
}

DatabaseConfiguration = MySQLConfiguration | PostgresConfiguration | SQLiteConfiguration


class DatabaseOutput(BaseSchema):
    documents: List[DataDocument]


def get_database_connection(
    configuration: DatabaseConfiguration,
    ssl_config: dict = None,
) -> sqlalchemy.engine.Connection:
    if configuration.engine not in DATABASES:
        raise ValueError(f"Unsupported database engine: {configuration.type}")

    if not ssl_config:
        if configuration.engine == DatabaseEngineType.POSTGRESQL:
            ssl_config = get_pg_ssl_config(configuration.dict())
        elif configuration.engine == DatabaseEngineType.MYSQL:
            ssl_config = get_mysql_ssl_config(configuration.dict())

    database_name = configuration.dbpath if configuration.engine == DatabaseEngineType.SQLITE else configuration.dbname

    connect_args: dict = {}

    if ssl_config:
        connect_args["ssl"] = ssl_config

    # Create URL
    db_url = sqlalchemy.engine.URL.create(
        drivername=DATABASES[configuration.engine]["driver"],
        username=configuration.user if hasattr(configuration, "user") else None,
        password=configuration.password if hasattr(configuration, "password") else None,
        host=configuration.host if hasattr(configuration, "host") else None,
        port=configuration.port if hasattr(configuration, "port") else None,
        database=database_name,
    )

    # Create engine
    engine = sqlalchemy.create_engine(db_url, connect_args=connect_args)

    # Connect to the database
    connection = engine.connect()

    return connection
