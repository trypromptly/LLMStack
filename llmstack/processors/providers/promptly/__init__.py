from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field

from llmstack.processors.providers.config import ProviderConfig


class ContentMimeType(str, Enum):
    TEXT = "text/plain"
    JSON = "application/json"
    HTML = "text/html"
    PNG = "image/png"
    JPEG = "image/jpeg"
    SVG = "image/svg+xml"
    PDF = "application/pdf"
    LATEX = "application/x-latex"

    def __str__(self):
        return self.value


class Content(BaseModel):
    data: str = Field(description="The content data")
    mime_type: ContentMimeType = Field(description="The content mime type", default=ContentMimeType.TEXT)


class GoogleSearchEngineConfig(BaseModel):
    api_key: str = Field(
        title="Google Custom Search API Key",
        description="API Key for Google Custom Search API",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    cx: str = Field(
        title="Google Custom Search Engine ID",
        description="Custom Search Engine ID for Google Custom Search API",
        default="",
        json_schema_extra={"advanced_parameter": False},
    )


SearchEngineConfig = Union[GoogleSearchEngineConfig]


class PromptlyProviderConfig(ProviderConfig):
    provider_slug: str = "promptly"
    search_engine: Optional[SearchEngineConfig] = Field(
        title="Search Engine",
        description="Search Engine Configuration",
        default=None,
    )
