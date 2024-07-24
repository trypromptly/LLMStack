import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, Field, PrivateAttr


class BaseProcessorBlock(BaseModel):
    slug: str
    provider_slug: str
    data: Optional[dict] = {}

    _processor_cls = PrivateAttr()

    def get_schema(self):
        return self._processor_cls.get_schema()

    def get_ui_schema(self):
        return self._processor_cls.get_ui_schema()

    @property
    def processor_cls(self):
        return self._processor_cls

    def get_default_data(self, **kwargs):
        return {}

    def to_dict(self):
        return {
            "slug": self.slug,
            "provider_slug": self.provider_slug,
            "schema": self.get_schema(),
            "ui_schema": self.get_ui_schema(),
            "data": self.get_default_data(),
        }


class PipelineSource(BaseProcessorBlock):
    def __init__(self, **data):
        from llmstack.data.sources.utils import get_source_cls

        super().__init__(**data)

        self._processor_cls = get_source_cls(slug=self.slug, provider_slug=self.provider_slug)


class PipelineDestination(BaseProcessorBlock):
    def __init__(self, **data):
        from llmstack.data.destinations.utils import get_destination_cls

        super().__init__(**data)

        self._processor_cls = get_destination_cls(slug=self.slug, provider_slug=self.provider_slug)


class PipelineTransformation(BaseProcessorBlock):
    def __init__(self, **data):
        from llmstack.data.transformations.utils import get_transformer_cls

        super().__init__(**data)

        self._processor_cls = get_transformer_cls(slug=self.slug, provider_slug=self.provider_slug)

    def get_default_data(self, **kwargs):
        return {**self.processor_cls.get_default_data(), **self.data}


class PipelineBlock(BaseModel):
    source: Optional[PipelineSource] = None
    transformations: Optional[List[PipelineTransformation]] = []
    destination: Optional[PipelineDestination] = None


class DataPipelineTemplate(BaseModel):
    slug: str
    name: str
    description: str
    pipeline: PipelineBlock

    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "pipeline": {
                "source": self.pipeline.source.to_dict() if self.pipeline.source else None,
                "transformations": [t.to_dict() for t in self.pipeline.transformations],
                "destination": self.pipeline.destination.to_dict() if self.pipeline.destination else None,
            },
        }


class DataDocument(BaseModel):
    id_: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID of the document.")
    name: Optional[str] = None
    text: Optional[str] = None
    content: Optional[str] = None
    mimetype: str = Field(default="text/plain", description="MIME type of the content.")
    metadata: Optional[dict] = None
    extra_info: Optional[dict] = None
    nodes: Optional[List[Any]] = None
    embeddings: Optional[List[float]] = None
    processing_errors: Optional[List[str]] = None
