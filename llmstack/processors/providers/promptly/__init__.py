from enum import Enum

from pydantic import BaseModel, Field


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
