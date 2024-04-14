from typing import Optional

from openai._models import BaseModel

__all__ = ["Image"]


class Image(BaseModel):
    b64_json: Optional[str] = None
    """
    The base64-encoded JSON of the generated image, if `response_format` is
    `b64_json`.
    """

    revised_prompt: Optional[str] = None
    """
    The prompt that was used to generate the image, if there was any revision to the
    prompt.
    """

    url: Optional[str] = None
    """The URL of the generated image, if `response_format` is `url` (default)."""

    name: Optional[str] = None

    mime_type: Optional[str] = None
    metadata: Optional[dict] = None

    def data_uri(self, include_name=False) -> str:
        mime_type = self.mime_type or "image/png"

        if include_name:
            try:
                name = self.name or f"image.{mime_type.split('/')[1]}"
            except Exception:
                name = "image"
            return f"data:{mime_type};name={name};base64,{self.b64_json}"
        return f"data:{mime_type};base64,{self.b64_json}"
