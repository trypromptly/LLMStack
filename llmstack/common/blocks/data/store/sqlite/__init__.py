from typing import List
from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument

class SQLiteConfiguration(BaseSchema):
    dbpath: str
    
class SQLiteOutput(BaseSchema):
    documents: List[DataDocument]