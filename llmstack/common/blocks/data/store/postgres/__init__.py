from base64 import b64decode
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import List, Optional

import psycopg2

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument


class SSLMode(str, Enum):
    disable = "disable"
    allow = "allow"
    prefer = "prefer"
    require = "require"
    verify_ca = "verify-ca"
    verify_full = "verify-full"


class PostgresConfiguration(BaseSchema):
    user: Optional[str]
    password: Optional[str]
    host: str = "127.0.0.1"
    port: int = 5432
    dbname: str
    use_ssl: bool = False
    sslmode: SSLMode = "prefer"
    sslrootcertFile: Optional[str]
    sslcertFile: Optional[str]
    sslkeyFile: Optional[str]

    class Config:
        schema_extra = {
            "order": ["host", "port", "user", "password"],
            "required": ["dbname"],
            "secret": ["password", "sslrootcertFile", "sslcertFile", "sslkeyFile"],
            "extra_options": ["sslmode", "sslrootcertFile", "sslcertFile", "sslkeyFile"],
        }


class PostgresOutput(BaseSchema):
    documents: List[DataDocument]


def _create_cert_file(configuration, key, ssl_config):
    file_key = key + "File"
    if file_key in configuration:
        with NamedTemporaryFile(mode="w", delete=False) as cert_file:
            cert_bytes = b64decode(configuration[file_key])
            cert_file.write(cert_bytes.decode("utf-8"))

        ssl_config[key] = cert_file.name


def _get_ssl_config(configuration: dict):
    ssl_config = {"sslmode": configuration.get("sslmode", "prefer")}

    _create_cert_file(configuration, "sslrootcert", ssl_config)
    _create_cert_file(configuration, "sslcert", ssl_config)
    _create_cert_file(configuration, "sslkey", ssl_config)

    return ssl_config


def get_pg_connection(configuration: dict):
    ssl_config = (
        _get_ssl_config(
            configuration,
        )
        if configuration.get("use_ssl")
        else {}
    )
    connection = psycopg2.connect(
        user=configuration.get("user"),
        password=configuration.get("password"),
        host=configuration.get("host"),
        port=configuration.get("port"),
        dbname=configuration.get("dbname"),
        async_=False,
        **ssl_config,
    )

    return connection
