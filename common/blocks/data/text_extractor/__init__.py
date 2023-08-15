from typing import List

from common.blocks.base.schema import BaseSchema
from common.blocks.data import DataDocument

class TextExtractorInput(BaseSchema):
    data: bytes
    mime_type: str
    id: str

class TextExtractorOutput(BaseSchema):
    documents: List[DataDocument]

class TextExtractorConfiguration(BaseSchema):
    pass