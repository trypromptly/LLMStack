from pydantic import BaseModel, PrivateAttr

from llmstack.common.blocks.base.schema import (
    CustomGenerateJsonSchema,
    get_ui_schema_from_json_schema,
)
from llmstack.data.schemas import DataDocument


class BaseDestination(BaseModel):
    _client = PrivateAttr(default=None)

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

    def add(self, document: DataDocument) -> DataDocument:
        raise NotImplementedError

    def delete(self, document: DataDocument) -> DataDocument:
        raise NotImplementedError

    def search(self, query: str, **kwargs):
        raise NotImplementedError

    def create_collection(self):
        pass

    def delete_collection(self):
        pass
