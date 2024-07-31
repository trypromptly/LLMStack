from typing import List

from pydantic import BaseModel

from llmstack.common.blocks.base.schema import (
    CustomGenerateJsonSchema,
    get_ui_schema_from_json_schema,
)
from llmstack.data.schemas import DataDocument


class BaseSource(BaseModel):
    @classmethod
    def slug(cls):
        raise NotImplementedError

    @classmethod
    def provider_slug(cls):
        raise NotImplementedError

    @classmethod
    def get_schema(cls):
        return cls.model_json_schema(schema_generator=CustomGenerateJsonSchema)

    @classmethod
    def get_ui_schema(cls):
        return get_ui_schema_from_json_schema(cls.get_schema())

    def get_data_documents(self, **kwargs) -> List[DataDocument]:
        raise NotImplementedError

    @classmethod
    def process_document(cls, document: DataDocument) -> DataDocument:
        return document
