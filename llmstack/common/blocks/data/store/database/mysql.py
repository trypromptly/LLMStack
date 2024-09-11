from typing import List, Optional

from pydantic import ConfigDict
from typing_extensions import Literal

from llmstack.common.blocks.base.schema import BaseSchema, StrEnum
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.database.constants import DatabaseEngineType

try:
    import MySQLdb

    enabled = True
except ImportError:
    enabled = False


class SSLMode(StrEnum):
    disabled = "DISABLED"
    preferred = "PREFERRED"
    required = "REQUIRED"
    verify_ca = "VERIFY_CA"
    verify_identity = "VERIFY_IDENTITY"


class MySQLConfiguration(BaseSchema):
    engine: Literal[DatabaseEngineType.MYSQL] = DatabaseEngineType.MYSQL
    user: Optional[str] = None
    password: Optional[str] = None
    host: str = "127.0.0.1"
    port: int = 3306
    dbname: str
    use_ssl: bool = False
    sslmode: SSLMode = "preferred"
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "order": ["host", "port", "user", "password"],
            "required": ["dbname"],
            "secret": ["password", "ssl_ca", "ssl_cert", "ssl_key"],
            "extra_options": ["sslmode", "ssl_ca", "ssl_cert", "ssl_key"],
        }
    )


class MySQLOutput(BaseSchema):
    documents: List[DataDocument]


def get_mysql_ssl_config(configuration: dict):
    if not configuration.get("use_ssl"):
        return {}

    ssl_config = {"sslmode": configuration.get("sslmode", "prefer")}

    if configuration.get("use_ssl"):
        config_map = {"ssl_mode": "preferred", "ssl_cacert": "ca", "ssl_cert": "cert", "ssl_key": "key"}
        for key, cfg in config_map.items():
            val = configuration.get(key)
            if val:
                ssl_config[cfg] = val

    return ssl_config


def get_mysql_connection(configuration: dict):
    params = dict(
        host=configuration.get("host"),
        user=configuration.get("user"),
        passwd=configuration.get("password"),
        db=configuration.get("dbname"),
        port=configuration.get("port", 3306),
        charset=configuration.get("charset", "utf8"),
        use_unicode=configuration.get("use_unicode", True),
        connect_timeout=configuration.get("connect_timeout", 60),
        autocommit=configuration.get("autocommit", True),
    )

    ssl_options = get_mysql_ssl_config()

    if ssl_options:
        params["ssl"] = ssl_options

    connection = MySQLdb.connect(**params)

    return connection
