from llmstack.common.blocks.base.schema import StrEnum


class DatabaseEngineType(StrEnum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
