from typing import List

from typing_extensions import Literal

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.database.constants import DatabaseEngineType


class SQLiteConfiguration(BaseSchema):
    engine: Literal[DatabaseEngineType.SQLITE] = DatabaseEngineType.SQLITE
    dbpath: str


class SQLiteOutput(BaseSchema):
    documents: List[DataDocument]
