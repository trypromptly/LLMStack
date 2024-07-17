from typing import List, Optional

from pydantic import BaseModel

from llmstack.common.blocks.base.schema import (
    CustomGenerateJsonSchema,
    get_ui_schema_from_json_schema,
)
from llmstack.common.blocks.data import DataDocument


class BaseSource(BaseModel):
    name: Optional[str] = None

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

    def get_data_documents(self) -> List[DataDocument]:
        raise NotImplementedError
