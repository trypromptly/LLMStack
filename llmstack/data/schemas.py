import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class BaseProcessorBlock(BaseModel):
    slug: str
    provider_slug: str
    data: Optional[dict] = {}


class PipelineBlock(BaseModel):
    source: Optional[BaseProcessorBlock] = None
    transformations: Optional[List[BaseProcessorBlock]] = []
    destination: Optional[BaseProcessorBlock] = None


class DataPipelineTemplate(BaseModel):
    slug: str
    name: str
    description: str
    pipeline: PipelineBlock


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
