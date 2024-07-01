from typing import List, TypeVar

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.database.constants import DatabaseEngineType
from llmstack.common.blocks.data.store.database.mysql import (
    MySQLConfiguration,
    get_mysql_ssl_config,
)
from llmstack.common.blocks.data.store.database.postgresql import (
    PostgresConfiguration,
    get_pg_ssl_config,
)
from llmstack.common.blocks.data.store.database.sqlite import SQLiteConfiguration

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

DatabaseConfigurationType = TypeVar("DatabaseConfigurationType", bound=DatabaseConfiguration)


class DatabaseOutput(BaseSchema):
    documents: List[DataDocument]


def get_database_configuration_class(engine: DatabaseEngineType) -> DatabaseConfigurationType:
    if engine == DatabaseEngineType.POSTGRESQL:
        return PostgresConfiguration
    elif engine == DatabaseEngineType.MYSQL:
        return MySQLConfiguration
    elif engine == DatabaseEngineType.SQLITE:
        return SQLiteConfiguration
    else:
        raise ValueError(f"Unsupported database engine: {engine}")


def get_ssl_config(configuration: DatabaseConfigurationType) -> dict:
    ssl_config = {}
    if configuration.engine == DatabaseEngineType.POSTGRESQL:
        ssl_config = get_pg_ssl_config(configuration.model_dump())
    elif configuration.engine == DatabaseEngineType.MYSQL:
        ssl_config = get_mysql_ssl_config(configuration.model_dump())
    return ssl_config


def get_database_connection(
    configuration: DatabaseConfigurationType,
    ssl_config: dict = None,
):
    import sqlalchemy

    if configuration.engine not in DATABASES:
        raise ValueError(f"Unsupported database engine: {configuration.engine}")

    if not ssl_config:
        ssl_config = get_ssl_config(configuration)

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
