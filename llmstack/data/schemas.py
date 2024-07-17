from typing import List, Optional

from pydantic import BaseModel


class BaseProcessorBlock(BaseModel):
    slug: str
    provider_slug: str


class PipelineBlock(BaseModel):
    source: Optional[BaseProcessorBlock] = None
    transformations: Optional[List[BaseProcessorBlock]] = []
    destination: Optional[BaseProcessorBlock] = None


class DataPipelineTemplate(BaseModel):
    slug: str
    name: str
    description: str
    pipeline: PipelineBlock
