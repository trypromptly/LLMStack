from typing import List

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument


class TextExtractorInput(BaseSchema):
    data: bytes
    mime_type: str
    id: str


class TextExtractorOutput(BaseSchema):
    documents: List[DataDocument]


class TextExtractorConfiguration(BaseSchema):
    pass
