from typing import Annotated, Union

from pydantic import BaseModel, Field

from llmstack.common.blocks.base.schema import (
    CustomGenerateJsonSchema,
    get_ui_schema_from_json_schema,
)
from llmstack.data.transformations.splitters.csv import CSVTextSplitter
from llmstack.data.transformations.splitters.llamindex import LlamIndexSentenceSplitter

TransformationComponent = Annotated[
    Union[CSVTextSplitter, LlamIndexSentenceSplitter], Field(title="Transformation Component")
]


class BaseTransformation(BaseModel):
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
