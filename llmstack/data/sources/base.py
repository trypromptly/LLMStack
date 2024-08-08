import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from llmstack.common.blocks.base.schema import (
    CustomGenerateJsonSchema,
    get_ui_schema_from_json_schema,
)


class DataDocument(BaseModel):
    id_: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID of the document.")
    name: Optional[str] = None
    text: Optional[str] = None
    text_objref: Optional[str] = None
    content: Optional[str] = None
    mimetype: str = Field(default="text/plain", description="MIME type of the content.")
    metadata: Optional[dict] = None
    extra_info: Optional[dict] = {}
    nodes: Optional[List[Any]] = None
    embeddings: Optional[List[float]] = None
    processing_errors: Optional[List[str]] = None
    datasource_uuid: Optional[str] = None
    request_data: Optional[dict] = {}
    node_ids: Optional[List[str]] = []


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
